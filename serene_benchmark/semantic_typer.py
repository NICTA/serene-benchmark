"""
Copyright (C) 2016 Data61 CSIRO
Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>

This module provides high level wrappers for semantic typers within this benchmark.
"""
import logging
import os

from serene.matcher.core import SchemaMatcher
from serene.api.exceptions import InternalError
from karmaDSL import KarmaSession
import time
import pandas as pd
import numpy as np

import sklearn.metrics

from neural_nets import Column, NN_Column_Labeler, hp, hp_mlp, hp_cnn
from keras import backend as K


domains = ["soccer", "dbpedia", "museum", "weather", "weapons"]
benchmark = {
    "soccer": ['bundesliga-2015-2016-rosters.csv', 'world_cup_2010_squads.csv',
               'fifa-soccer-12-ultimate-team-data-player-database.csv', 'world_cup_2014_squads.csv',
               'all_world_cup_players.csv', 'mls_players_2015.csv', 'world_cup_squads.csv',
               'players.csv', '2014 WC french.csv', 'uefa_players.csv', 'world_cup_player_ages.csv',
               'WM 2014 Alle Spieler - players fifa.csv'],
    "dbpedia": ['s5.txt', 's2.txt', 's6.txt',
                's3.txt', 's4.txt', 's9.txt',
                's8.txt', 's7.txt', 's10.txt', 's1.txt'],
    "museum": ['s02-dma.csv', 's26-s-san-francisco-moma.json', 's27-s-the-huntington.json',
               's16-s-hammer.xml', 's20-s-lacma.xml', 's15-s-detroit-institute-of-art.json',
               's28-wildlife-art.csv', 's04-ima-artworks.xml', 's25-s-oakland-museum-paintings.json',
               's29-gilcrease.csv', 's05-met.json', 's13-s-art-institute-of-chicago.xml',
               's14-s-california-african-american.json', 's07-s-13.json', 's21-s-met.json',
               's12-s-19-artworks.json', 's08-s-17-edited.xml', 's19-s-indianapolis-artworks.xml',
               's11-s-19-artists.json', 's22-s-moca.xml', 's17-s-houston-museum-of-fine-arts.json',
               's18-s-indianapolis-artists.xml', 's23-s-national-portrait-gallery.json',
               's03-ima-artists.xml', 's24-s-norton-simon.json', 's06-npg.json',
               's09-s-18-artists.json', 's01-cb.csv'],
    "weather": ['w1.txt', 'w3.txt', 'w2.txt', 'w4.txt'],
    "weapons": ["www.theoutdoorstrader.com.csv", "www.tennesseegunexchange.com.csv",
                "www.shooterswap.com.csv", "www.nextechclassifieds.com.csv", "www.msguntrader.com.csv",
                "www.montanagunclassifieds.com.csv", "www.kyclassifieds.com.csv",
                "www.hawaiiguntrader.com.csv", "www.gunsinternational.com.csv",
                "www.floridaguntrader.com.csv", "www.floridagunclassifieds.com.csv",
                "www.elpasoguntrader.com.csv", "www.dallasguns.com.csv",
                "www.armslist.com.csv", "www.alaskaslist.com.csv"
                ]
}


class SemanticTyper(object):
    """
    Abstract model for semantic labelling/typing.
    Evaluation will be based on this abstract model.
    Fixed for 4 domains for now.
    """
    if "SERENEPATH" in os.environ:
        data_dir = os.path.join(os.environ["SERENEPATH"], "sources")
        label_dir = os.path.join(os.environ["SERENEPATH"], "labels")
    else:
        data_dir = os.path.join("data", "sources")
        label_dir = os.path.join("data", "labels")


    allowed_sources = []
    for sources in benchmark.values():
        # only these sources can be used for training or testing by different classifiers of SemanticTyper
        allowed_sources += sources

    metrics = ['categorical_accuracy', 'fmeasure', 'MRR']  # list of performance metrics to compare column labelers with
    metrics_average = 'macro'  # 'macro', 'micro', or 'weighted'

    def __init__(self, model_type, description="", debug_csv=None):
        self.model_type = model_type
        self.description = description
        self.debug_csv = debug_csv

    def reset(self):
        pass

    def define_training_data(self, train_sources, train_labels):
        pass

    def train(self):
        pass

    def predict(self, source):
        pass

    def evaluate(self, predicted_df):
        """
        Evaluate the performance of the model.
        :param predicted_df: Dataframe which contains predictions and obligatory columns
            user_label
            label
            scores_*
        :return:
        """
        logging.info("Evaluating model: {}".format(self.model_type))
        y_true = predicted_df["user_label"].as_matrix()
        y_pred = predicted_df["label"].as_matrix()

        logging.debug("y_true: {}".format(y_true))
        logging.debug("y_pred: {}".format(y_pred))

        scores_cols = [col for col in predicted_df.columns if col.startswith("scores_")]
        logging.debug("scores_cols: {}".format(scores_cols))

        y_pred_scores = predicted_df[scores_cols].copy().fillna(value=0).as_matrix()
        logging.debug("predicted scores: {}".format(y_pred_scores))
        y_true_scores = []
        for lab in predicted_df["user_label"]:
            trues = [0 for _ in range(len(scores_cols))]
            if "scores_"+lab in scores_cols:
                trues[scores_cols.index("scores_"+lab)] = 1
            y_true_scores.append(trues)
        logging.debug("true scores: {}".format(y_true_scores))
        y_true_scores = np.array(y_true_scores)

        performance = {"model": self.model_type, "description": self.description}
        if 'categorical_accuracy' in self.metrics:
            logging.info("Calculating categorical accuracy for {}".format(self))
            performance['categorical_accuracy'] = sklearn.metrics.accuracy_score(y_true,
                                                                                 y_pred)  # np.mean(y_pred == y_true)
        if 'fmeasure' in self.metrics:
            logging.info("Calculating fmeasure for {}".format(self))
            if len(y_true) == 2:
                performance['fmeasure'] = sklearn.metrics.f1_score(y_true, y_pred,
                                                                   average=self.metrics_average,
                                                                   pos_label=y_true[0])
            else:
                performance['fmeasure'] = sklearn.metrics.f1_score(y_true, y_pred, average=self.metrics_average)
        if 'MRR' in self.metrics:
            logging.info("Calculating MRR for {}".format(self))
            performance['MRR'] = sklearn.metrics.label_ranking_average_precision_score(y_true_scores, y_pred_scores)
        logging.info("Calculated performance: {}".format(performance))
        print("Calculated performance: {}".format(performance))
        return pd.DataFrame(performance, index=[0])




    def __str__(self):
        return "<SemanticTyper: model_type={}, description={}>".format(self.model_type, self.description)


class DINTModel(SemanticTyper):
    """
    Wrapper for DINT schema matcher.
    """
    def __init__(self, schema_matcher, feature_config, resampling_strategy, description, debug_csv=None):
        """
        Initializes DINT model with the specified feature configuration and resampling strategy.
        The model gets created at schema_matcher server.
        :param schema_matcher: SchemaMatcherSession instance
        :param feature_config: Dictionary with feature configuration for DINT
        :param resampling_strategy: Resampling strategy
        :param description: Description
        """
        logging.info("Initializing DINT model.")
        if not(type(schema_matcher) is SchemaMatcher):
            logging.error("DINTModel init: SchemaMatcher instance required.")
            raise InternalError("DINTModel init", "SchemaMatcher instance required")

        super().__init__("DINTModel", description=description, debug_csv=debug_csv)

        self.server = schema_matcher
        self.feature_config = feature_config
        self.resampling_strategy = resampling_strategy
        self.classifier = None
        self.datasets = [] # list of associated datasets for this model

    def reset(self):
        """
        Reset the model to the blank untrained state.
        We accomplish this by first deleting the existing model from the schema matcher server and then creating the
        fresh model at the server.
        :return:
        """
        logging.info("Resetting DINTModel.")
        # now serene will not allow dataset deletion if there is a dependent model
        if self.classifier:
            try:
                self.server.remove_model(self.classifier)
            except Exception as e:
                logging.warning("Failed to delete DINTModel: {}".format(e))
        for ds in self.datasets:
            try:
                self.server.remove_dataset(ds)
            except Exception as e:
                logging.warning("Failed to delete dataset: {}".format(e))

        self.classifier = None

    def _construct_labelData(self, matcher_dataset, filepath, header_column="column_name", header_label="class"):
        """
        We want to construct a dictionary {column_id:class_label} for the dataset based on a .csv file.
        This method reads in .csv as a Pandas data frame, selects columns "column_name" and "class",
        drops NaN and converts these two columns into dictionary.
        We obtain a lookup dictionary
        where the key is the column name and the value is the class label.
        Then by using column_map the method builds the required dictionary.

        Args:
            filepath: string where .csv file is located.
            header_column: header for the column with column names
            header_label: header for the column with labels

        Returns: dictionary

        """
        logging.debug("--> Labels in {}".format(filepath))
        label_data = {}  # we need this dictionary (column_id, class_label)
        try:
            frame = pd.read_csv(filepath, na_values=[""], dtype={header_column: 'str'})
            logging.debug("  --> headers {}".format(frame.columns))
            logging.debug("  --> dtypes {}".format(frame.dtypes))
            # dictionary (column_name, class_label)scr
            name_labels = frame[[header_column, header_label]].dropna().set_index(header_column)[header_label].to_dict()
            column_map = [(col.id, col.name) for col in matcher_dataset.columns]
            logging.debug("  --> column_map {}".format(column_map))
            for col_id, col_name in column_map:
                if col_name in name_labels:
                    label_data[int(col_id)] = name_labels[col_name]
        except Exception as e:
            raise InternalError("construct_labelData", e)

        return label_data

    def define_training_data(self, train_sources, train_labels=None):
        """

        :param train_sources: List of sources. For now it's hard coded for the allowed_sources.
        :param train_labels: List of files with labels, optional. If not present, the default labels will be used.
        :return:
        """
        logging.info("Defining training data for DINTModel.")
        label_dict = {}
        for idx, source in enumerate(train_sources):
            if source not in self.allowed_sources:
                logging.warning("Source '{}' not in allowed_sources. Skipping it.".format(source))
                continue
            # upload source to the schema matcher server
            matcher_dataset = self.server.create_dataset(file_path=os.path.join(self.data_dir, source+".csv"),
                                                         description="traindata",
                                                         type_map={})
            self.datasets.append(matcher_dataset)

            # construct dictionary of labels for the uploaded dataset
            try:
                label_dict.update(self._construct_labelData(matcher_dataset, train_labels[idx]))
            except:
                # in case train_labels are not provided, we take default labels from the serene_benchmark
                label_dict.update(self._construct_labelData(matcher_dataset,
                                                      filepath=os.path.join(self.label_dir, source+".columnmap.txt"),
                                                      header_column="column_name",
                                                      header_label="semantic_type"))
            logging.debug("DINT model label_dict for source {} updated: {}".format(source, label_dict))

        # create model on the server with the labels specified
        logging.debug("Creating model on the DINT server with proper config.")
        classes = list(set(label_dict.values())) + ["unknown"]
        self.classifier = self.server.create_model(self.feature_config,
                                                   classes=classes,
                                                   description=self.description,
                                                   labels=label_dict,
                                                   resampling_strategy=self.resampling_strategy,
                                                   num_bags=50,
                                                   bag_size=100)

        logging.debug("DINT model created on the server!")

        return True

    def train(self):
        """
        Train DINTModel and return run time.
        :return: run time in seconds
        """
        logging.info("Training DINTModel:")
        logging.info("  model type: {}".format(type(self.classifier)))
        start = time.time()
        tr = self.classifier.train()
        return time.time() - start

    def predict(self, source):
        """
        Prediction with DINTModel for the source.
        :param source:
        :return: A pandas dataframe with obligatory columns: column_name, source_name, label, user_label, scores
        """
        logging.info("Predicting with DINTModel for source {}".format(source))
        if source not in self.allowed_sources:
            logging.warning("Source '{}' not in allowed_sources. Skipping it.".format(source))
            return None
        # upload source to the schema matcher server
        matcher_dataset = self.server.create_dataset(file_path=os.path.join(self.data_dir, source + ".csv"),
                                                     description="testdata",
                                                     type_map={})
        self.datasets.append(matcher_dataset)
        logging.debug("Test data added to the server.")
        start = time.time()
        predict_df = self.classifier.predict(matcher_dataset.id).copy()
        predict_df["running_time"] = time.time() - start
        column_map = dict([(col.id, col.name) for col in matcher_dataset.columns])
        predict_df["column_name"] = predict_df["column_id"].apply(lambda x: column_map[x])
        predict_df["source_name"] = source
        predict_df["model"] = self.model_type
        predict_df["model_description"] = self.description
        label_dict = self._construct_labelData(matcher_dataset,
                                             filepath=os.path.join(self.label_dir, source + ".columnmap.txt"),
                                             header_column="column_name",
                                             header_label="semantic_type")
        predict_df["user_label"] = predict_df["column_id"].apply(
            lambda x: label_dict[x] if x in label_dict else 'unknown')
        return predict_df


class KarmaDSLModel(SemanticTyper):
    """
    Wrapper for Karma DSL semantic labeller.
    KarmaDSL server can hold only one model.
    """
    def __init__(self, karma_session, description, debug_csv=None):
        logging.info("Initializing KarmaDSL model.")
        if not (type(karma_session) is KarmaSession):
            logging.error("KarmaDSLModel init: KarmaSession instance required.")
            raise InternalError("KarmaDSLModel init", "KarmaSession instance required")

        super().__init__("KarmaDSL", description=description,debug_csv=debug_csv)
        self.karma_session = karma_session
        self.karma_session.reset_semantic_labeler() # we immediately reset their semantic labeller
        self.folder_names = None
        self.train_sizes = None

    def reset(self):
        self.karma_session.reset_semantic_labeler()
        self.folder_names = None
        self.train_sizes = None

    def define_training_data(self, train_sources, train_labels=None):
        """

        :param train_sources:
        :param train_labels: is not used here...
        :return:
        """
        # copy train_sources
        logging.info("Defining train data for KarmaDSL: {}".format(
            self.karma_session.post_folder("train_data", train_sources)))
        self.folder_names = ["train_data"]
        self.train_sizes = [len(train_sources)-1]  # TODO: check that it should be exactly this
        return True

    def train(self):
        start = time.time()
        if self.folder_names and self.train_sizes:
            logging.info("Training KarmaDSL...")
            self.karma_session.train_model(self.folder_names, self.train_sizes)
            return time.time() - start
        logging.error("KarmaDSL cannot be trained since training data is not specified.")
        raise InternalError("KarmaDSL train", "training data absent")

    def predict(self, source):
        """

        :param source:
        :return:
        """
        if source not in self.allowed_sources:
            logging.warning("Source '{}' not in allowed_sources. Skipping it.".format(source))
            return None
        resp = self.karma_session.post_folder("test_data", [source])
        logging.info("Posting source {} to karma dsl server: {}".format(source,resp))
        predicted = self.karma_session.predict_folder("test_data")
        logging.info("KarmaDSL prediction finished: {}".format(predicted["running_time"]))
        print("     KarmaDSL prediction finished: {}".format(predicted["running_time"]))
        df = []
        for val in predicted["predictions"]:
            correct_lab = val["correct_label"] if val["correct_label"] is not None else 'unknown'
            row = {"column_name": val["column_name"],
                   "source_name": source,
                   "user_label": correct_lab,
                   "model": self.model_type,
                   "model_description": self.description
                   }
            max = 0
            label = "unknown"
            for sc in val["scores"]:
                row["scores_"+sc[1]] = sc[0]
                if sc[0] > max:
                    max = sc[0]
                    label = sc[1]
            row["label"] = label
            df.append(row)
        df = pd.DataFrame(df)
        df["running_time"] = predicted["running_time"]
        return df


class NNetModel(SemanticTyper):
    """
        Wrapper for semantic labeller powered by Neural Network models (NN_Column_Labeler class from nn_column_labeler).
        Originally the labeller can hold multiple classifier models (e.g., 'cnn@charseq', 'mlp@charfreq', etc.,)
        but here we assume 1 model per instance of NNetModel, for the purpose of benchmarking.

        If only one classifier type is given in the 'classifier_types' argument
        (as a list, e.g., classifier_types=['cnn@charseq']),
        this works for the following classifier types only:
        'cnn@charseq', 'mlp@charseq' (poor performance!), 'rf@charseq'; 'mlp@charfreq', 'rf@charfreq'
    """
    def _read(self, source, label_source=None):
        """
        Read columns from source, and return them as a list of Column objects
        (as defined in neural_nets.museum_data_reader).
        :param source:
        :param label_source:
        :return:
        """
        filename = os.path.join(self.data_dir, source+".csv")
        if label_source is None:
            label_filename = os.path.join(self.label_dir, source + ".columnmap.txt")
        else:
            label_filename = os.path.join(self.label_dir, label_source)
        logging.debug("Reading source for NNet: {}".format(filename))
        df = pd.read_csv(filename, dtype=str)  # read the data source as a DataFrame
        # labels = pd.read_csv(label_filename)   # read the semantic labels of columns in df

        labels_frame = pd.read_csv(label_filename, na_values=[""], dtype={'column_name': 'str'})
        # dictionary (column_name, class_label)
        labels = labels_frame[['column_name', 'semantic_type']].dropna().set_index(
            'column_name')['semantic_type'].to_dict()
        logging.debug("Labels read for NNet.")

        source_cols = []
        for c in df.columns:
            # label = str(labels.get_value(labels[labels['column_name'] == c].index[0], 'semantic_type'))   # extract semantic label of column c
            if c in labels:
                label = labels[c]
            else:
                label = 'unknown'
            col = Column(filename=filename, colname=c, title=label, lines=list(df[c]))
            source_cols.append(col)

        return source_cols

    def __init__(self, classifier_types, description, add_headers=False, p_header=0, debug_csv=None):
        """
        Initialize NNetModel.
        :param classifier_types:
        :param description:
        :param add_headers:
        :param p_header:
        :param debug_csv:
        """
        classifier_type = classifier_types[0]
        logging.info("Initializing NNetModel with {} classifier...".format(classifier_type))
        super().__init__("NNetModel", description=description, debug_csv=debug_csv)
        self.classifier_type = classifier_type
        self.add_headers = add_headers
        self.p_header = p_header
        self.labeler = None
        self.train_cols = None   # placeholder for a list of training cols (Column objects)

    def reset(self):
        """
        Reset the NNetModel.
        """
        logging.info("Resetting NNetModel...")
        K.clear_session()  # Destroys the current TF graph and creates a new one. Useful to avoid clutter from old models / layers.
        self.train_cols = None
        self.labeler = None

    def define_training_data(self, train_sources, train_labels=None):
        """
        Extract training columns from train_sources, and assign semantic labels to them.
        The result should be self.train_cols - a list of Column objects (defined in museum_data_reader)
        to pass to labeler in self.train()
        :param train_sources:
        :param train_labels:
        :return:
        """
        logging.info("Defining training data for NNetModel...")
        self.train_cols = []
        if train_labels is None:
            for source in train_sources:
                self.train_cols += self._read(source)
        else:
            for source, label in zip(train_sources, train_labels):
                self.train_cols += self._read(source, label)

        logging.info("NNetModel: Training data contains {} columns from {} sources".format(len(self.train_cols), len(train_sources)))

    def train(self):
        """
        Create an instance of NN_Column_Labeler, perform bagging,
        feature preparation, and training of the underlying classifier(s).
        """
        logging.info("NNetModel training starts...")
        start = time.time()
        self.labeler = NN_Column_Labeler([self.classifier_type],
                                         self.train_cols,
                                         split_by=hp['split_by'],
                                         test_frac=0, # no further splitting into train and test sets, i.e., use train_cols as all_cols
                                         add_headers=self.add_headers,
                                         p_header=self.p_header)
        # TODO: rewrite NN_Column_Labeler to be initialized with train_cols only, instead of all_cols followed by internal splitting of all_cols into train, valid, ant test sets of columns

        # Train self.labeler:
        self.labeler.train(evaluate_after_training=False)

        return time.time() - start

    def predict(self, source):
        """
        Predict labels for all columns in source.
        :param source:
        :return:
        """
        if source not in self.allowed_sources:
            logging.warning("Source '{}' not in allowed_sources. Skipping it.".format(source))
            return None
        # First, we need to extract query Column objects from source:
        query_cols = self._read(source)
        logging.info("NNetModel: Predicting for {} columns from {} sources".format(len(query_cols), len(source)))

        true_labels = [c.title for c in query_cols]
        logging.debug("NNetModel predict: True labels set.")

        # Then, pass these query cols to self.labeler.predict as
        start = time.time()
        y_pred_proba = self.labeler.predict_proba(query_cols)
        logging.debug("NNetModel predict: Class probabilities calculated.")

        # predictions = []
        predictions_proba = [y_proba[self.classifier_type] for y_proba in y_pred_proba]

        time_elapsed = time.time() - start
        # Finally, convert predictions to the pd dataframe in the required format:
        logging.info("NNetModel predict: Converting to dataframe...")
        predictions_proba_dict = []
        for i, c in enumerate(query_cols):
            row = {"column_name": c.colname,
                   "source_name": source,
                    "user_label": c.title,
                    "model": self.model_type,
                    "model_description": self.description
                    }
            preds = predictions_proba[i]   # numpy array of probabilities for the i-th column
            max = 0
            label = "unknown"
            for j, score in enumerate(preds):
                class_name = self.labeler.inverted_lookup[j]
                logging.debug("     NNetModel predict: class_name found {}".format(class_name))
                row["scores_"+str(class_name)] = score
                if score > max:
                    max = score
                    label = class_name
            row["label"] = label
            row["confidence"] = max
            row["running_time"] = time_elapsed
            predictions_proba_dict.append(row)
        logging.info("NNetModel predict: success.")
        # Return the predictions df:
        return pd.DataFrame(predictions_proba_dict)