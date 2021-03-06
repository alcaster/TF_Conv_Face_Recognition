import os
from functools import partial

import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder


def _parse_function(img_size, num_classes, is_train, filename, label, scope=None):
    with tf.name_scope(scope, 'parse', [filename, label]):
        image_string = tf.read_file(filename)
        image_decoded = tf.image.decode_png(image_string, channels=3)
        image_decoded = tf.cast(image_decoded, tf.float32)
        image = tf.image.resize_images(image_decoded, [img_size, img_size])
        if is_train:
            image = _augment_image(image)  # [batch_size, img_size, img_size, channels]
        label = tf.one_hot(label, num_classes)

        return image, label


def _augment_image(image: tf.Tensor, scope=None) -> tf.Tensor:
    with tf.name_scope(scope, 'augmentation', image):
        image = tf.image.random_flip_left_right(image)
        image = tf.image.random_brightness(image, 0.4)
        image = tf.image.random_contrast(image, lower=0.4, upper=1.4)
        image = tf.image.random_hue(image, 0.4)
    return image


def get_train_valid_iterators(data_dir: str, test_set_size: float, epochs: int, batch_size: int, img_size: int,
                              num_parallel: int, buffer_size: int) -> (
        tf.data.Iterator, tf.placeholder, tf.data.Iterator, tf.data.Iterator, tuple):
    le = LabelEncoder()
    images_paths, labels = get_images_paths(data_dir)
    labels = le.fit_transform(labels)
    num_classes = len(set(labels))
    dataset_size = len(labels)
    X_train, X_test, y_train, y_test = train_test_split(images_paths, labels, test_size=test_set_size)

    _parse_w_args = partial(_parse_function, img_size, num_classes, True)
    dataset_train = tf.data.Dataset.from_tensor_slices((X_train, y_train))
    dataset_train = dataset_train.shuffle(buffer_size=buffer_size)
    dataset_train = dataset_train.map(_parse_w_args, num_parallel_calls=num_parallel)
    dataset_train = dataset_train.repeat(epochs)
    dataset_train = dataset_train.batch(batch_size)

    _parse_w_args = partial(_parse_function, img_size, num_classes, False)
    dataset_valid = tf.data.Dataset.from_tensor_slices((X_test, y_test))
    dataset_valid = dataset_valid.map(_parse_w_args, num_parallel_calls=num_parallel)
    dataset_valid = dataset_valid.batch(batch_size)

    handle = tf.placeholder(tf.string, shape=[])
    iterator = tf.data.Iterator.from_string_handle(
        handle, dataset_train.output_types, dataset_train.output_shapes)
    training_iterator = dataset_train.make_one_shot_iterator()
    validation_iterator = dataset_valid.make_one_shot_iterator()

    return iterator, handle, training_iterator, validation_iterator, (
        dataset_size * (1 - test_set_size), dataset_size * test_set_size)


def get_test_iterator(data_dir, img_size, batch_size, num_parallel):
    images_paths, labels = get_images_paths(data_dir)
    le = LabelEncoder()
    labels = le.fit_transform(labels)
    num_classes = len(set(labels))
    dataset_size = len(labels)
    _parse_w_args = partial(_parse_function, img_size, num_classes, False)
    dataset_test = tf.data.Dataset.from_tensor_slices((images_paths, labels))
    dataset_test = dataset_test.map(_parse_w_args, num_parallel_calls=num_parallel)
    dataset_test = dataset_test.batch(batch_size)
    test_iterator = dataset_test.make_one_shot_iterator()
    return test_iterator, dataset_size


def get_images_paths(data_dir):
    images_paths, labels = [], []
    for categ in os.listdir(data_dir):
        if not categ.startswith('.') and categ != "saved.npy":
            for file in os.listdir(f"{data_dir}/{categ}"):
                if not file.startswith('.'):
                    labels.append(categ)
                    images_paths.append(f"{data_dir}/{categ}/{file}")
    return images_paths, labels
