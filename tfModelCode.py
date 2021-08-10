print("starting imports")
import tensorflow as tf
import json
import numpy as np
import os
from tensorflow.keras.callbacks import ReduceLROnPlateau

print("done with imports")
print(tf.__version__)

INPUT_TENSOR_NAME = "input_16_input"  # Watch out, it needs to match the name of the first layer + "_input"
HEIGHT = 250
WIDTH = 250
DEPTH = 3
IM_SIZE = (250, 250)
NUM_CLASSES = 3
BATCH_SIZE = 8
CLASSES = ["Priority", "Roundabout", "Signal"]


def keras_model_fn(train_batches, val_batches):
    
    data_augmentation = tf.keras.Sequential([
      tf.keras.layers.experimental.preprocessing.RandomFlip('horizontal'),
      tf.keras.layers.experimental.preprocessing.RandomRotation(0.2),
    ])
    
    preprocess_input = tf.keras.applications.efficientnet.preprocess_input    
    
    IMG_SIZE=IM_SIZE + (3,)
    
    base_model = tf.keras.applications.efficientnet.EfficientNetB7(
        include_top=False,
        weights="imagenet",
        input_shape=IMG_SIZE,classes=3
    )
    
    image_batch, label_batch = next(iter(train_dataset))
    feature_batch = base_model(image_batch)

    global_average_layer = tf.keras.layers.GlobalAveragePooling2D()
    feature_batch_average = global_average_layer(feature_batch)
    
    prediction_layer = tf.keras.layers.Dense(len(CLASSES), activation='softmax',name='softmax')
    prediction_batch = prediction_layer(feature_batch_average)
    inputs = tf.keras.Input(shape=(250, 250, 3))
    x = data_augmentation(inputs)
    x = preprocess_input(x)
    x = base_model(x, training=False)
    x = global_average_layer(x)
    x = tf.keras.layers.Dropout(0.2)(x)
    outputs = prediction_layer(x)
    model = tf.keras.Model(inputs, outputs)
    base_learning_rate = 0.0002
    model.compile(loss=tf.keras.losses.CategoricalCrossentropy(),
                  optimizer = tf.keras.optimizers.SGD(),
                  metrics=['accuracy'])

    # Estimate class weights for unbalanced dataset
    # class_weights = class_weight.compute_class_weight(
    #                'balanced',
    #                 np.unique(train_batches.classes),
    #                 train_batches.classes)

    ReduceLR = ReduceLROnPlateau(monitor='val_loss', factor=0.2,
                                 patience=5, min_lr=3e-4)

    model.fit(train_batches,
                        validation_data=val_batches,
                        epochs=30,
                        callbacks=[ReduceLR])
    return model


def train_input_fn(training_dir, hyperparameters):
    return _input(tf.estimator.ModeKeys.TRAIN, batch_size=BATCH_SIZE, data_dir=training_dir)


def eval_input_fn(training_dir, hyperparameters):
    return _input(tf.estimator.ModeKeys.EVAL, batch_size=BATCH_SIZE, data_dir=training_dir)


import os
# from tensorflow.python.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.preprocessing import image_dataset_from_directory



def _input(mode, batch_size, data_dir):
    assert os.path.exists(data_dir), ("Unable to find images resources for input, are you sure you downloaded them ?")


    train_dataset = image_dataset_from_directory(data_dir + '/train',
                                 shuffle=True,
                                 batch_size=BATCH_SIZE,
                                 image_size=IM_SIZE,label_mode='categorical')
    
    images, labels = next(iter(train_dataset))

    return {INPUT_TENSOR_NAME: images}, labels


def serving_input_fn(hyperparameters):
    # Here it concerns the inference case where we just need a placeholder to store
    # the incoming images ...
    tensor = tf.placeholder(tf.float32, shape=[None, HEIGHT, WIDTH, DEPTH])
    inputs = {INPUT_TENSOR_NAME: tensor}
    return tf.estimator.export.ServingInputReceiver(inputs, inputs)


def _parse_args():
    import argparse

    parser = argparse.ArgumentParser()

    # Data, model, and output directories
    # model_dir is always passed in from SageMaker. By default this is a S3 path under the default bucket.
    parser.add_argument('--model_dir', type=str)
    parser.add_argument('--sm-model-dir', type=str, default=os.environ.get('SM_MODEL_DIR'))
    parser.add_argument('--train', type=str, default=os.environ.get('SM_CHANNEL_TRAINING'))
    parser.add_argument('--hosts', type=list, default=json.loads(os.environ.get('SM_HOSTS')))
    parser.add_argument('--current-host', type=str, default=os.environ.get('SM_CURRENT_HOST'))

    return parser.parse_known_args()


if __name__ == "__main__":
    print("starting in main")
    args, unknown = _parse_args()

    data_dir = args.train
    
    train_dataset=image_dataset_from_directory(data_dir + '/train',
                                 shuffle=True,
                                 batch_size=BATCH_SIZE,
                                 image_size=IM_SIZE,label_mode='categorical')


    valid_dataset = image_dataset_from_directory(data_dir + '/test',
                                                    image_size=IM_SIZE,
                                                    label_mode='categorical', shuffle=False,
                                                    batch_size=BATCH_SIZE)

    # Create the Estimator
    print("calling model fit")
    junction_classifier = keras_model_fn(train_dataset, valid_dataset)
    print("about to save")

    if args.current_host == args.hosts[0]:
        
        # save model to an S3 directory with version number '00000001'
        # sound_classifier.save(os.path.join(args.sm_model_dir, '000000001'), 'sound_model.h5')
        tf.keras.models.save_model(junction_classifier, os.path.join(args.sm_model_dir, 'tf000000001/1'))