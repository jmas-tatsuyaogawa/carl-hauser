import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import pathlib
import logging
import json
from shutil import copyfile

import utility_lib.json_class as json_class
import utility_lib.stats_lib as stats_lib
import utility_lib.filesystem_lib as filesystem_lib
import configuration
import results

''' Example of values : 
vegetables = ["cucumber", "tomato", "lettuce", "asparagus",
              "potato", "wheat", "barley"]
farmers = ["Farmer Joe", "Upland Bros.", "Smith Gardening",
           "Agrifun", "Organiculture", "BioGoods Ltd.", "Cornylee Corp."]

harvest = np.array([[0.8, 2.4, 2.5, 3.9, 0.0, 4.0, 0.0],
                    [2.4, 0.0, 4.0, 1.0, 2.7, 0.0, 0.0],
                    [1.1, 2.4, 0.8, 4.3, 1.9, 4.4, 0.0],
                    [0.6, 0.0, 0.3, 0.0, 3.1, 0.0, 0.0],
                    [0.7, 1.7, 0.6, 2.6, 2.2, 6.2, 0.0],
                    [1.3, 1.2, 0.0, 0.0, 0.0, 3.2, 5.1],
                    [0.1, 2.0, 0.0, 1.4, 0.0, 1.9, 6.3]])
'''
# From : https://matplotlib.org/gallery/images_contours_and_fields/image_annotated_heatmap.html

class Graphe(configuration.JSON_parsable_Dict):
    '''
    Datastructure to handle graphes
    Inherit from JSON_parsable_dict to allow to export it in a JSON with a custom JSON Encoder
    '''
    def __init__(self):
        self.nodes = []
        self.edges = []

    def load_from_json(self, json):
        if isinstance(json, Graphe):
            self.nodes = json.nodes
            self.edges = json.edges
        else :
            self.nodes = json["nodes"]
            self.edges = json["edges"]


class Graph_handler():
    def __init__(self):
        self.ord = None
        self.abs = None
        self.values = None

    # ============================== --------------------------------  ==============================
    #                                    Public useful methods

    def set_values(self, ordo, absi, values):
        '''
        Set input values of the graph to be created
        :param ordo:
        :param absi:
        :param values:
        :return:
        '''
        self.ord = ordo
        self.abs = absi
        self.values = np.array(values)

    def get_matrix(self):
        '''
        Create the matrix of values / heatmap thanks to stored values
        :return:
        '''
        fig, ax = plt.subplots(figsize=(20, 14), dpi=200)

        im, cbar = self.heatmap(self.values, self.ord, self.abs, ax=ax,
                                cmap="YlGn", cbarlabel="Similarity (1 = same)")
        # texts = self.annotate_heatmap(im, valfmt="{x:.1f}")

        return fig

    def show_matrix(self):
        '''
        Show the matrix of values (call get_matrix to create it inside)
        :return:
        '''
        fig = self.get_matrix()
        # fig.tight_layout()
        plt.show()

    def save_matrix(self, output_file: pathlib.Path):
        '''
        Save the matrix of values to the defined location (call get_matrix to create it inside)
        :return:
        '''
        fig = self.get_matrix()

        fig.tight_layout()
        plt.savefig(str(output_file))

    # ============================== --------------------------------  ==============================
    #                                   Graphical operation

    @staticmethod
    def heatmap(data, row_labels, col_labels, ax=None,
                cbar_kw={}, cbarlabel="", **kwargs):
        """
        Create a heatmap from a numpy array and two lists of labels.

        Arguments:
            data       : A 2D numpy array of shape (N,M)
            row_labels : A list or array of length N with the labels
                         for the rows
            col_labels : A list or array of length M with the labels
                         for the columns
        Optional arguments:
            ax         : A matplotlib.axes.Axes instance to which the heatmap
                         is plotted. If not provided, use current axes or
                         create a new one.
            cbar_kw    : A dictionary with arguments to
                         :meth:`matplotlib.Figure.colorbar`.
            cbarlabel  : The label for the colorbar
        All other arguments are directly passed on to the imshow call.
        """

        if not ax:
            ax = plt.gca()

        # Plot the heatmap
        im = ax.imshow(data, **kwargs)

        # Create colorbar
        cbar = ax.figure.colorbar(im, ax=ax, **cbar_kw)
        cbar.ax.set_ylabel(cbarlabel, rotation=-90, va="bottom")

        # We want to show all ticks...
        ax.set_xticks(np.arange(data.shape[1]))
        ax.set_yticks(np.arange(data.shape[0]))
        # ... and label them with the respective list entries.
        ax.set_xticklabels(col_labels)
        ax.set_yticklabels(row_labels)

        # Let the horizontal axes labeling appear on top.
        ax.tick_params(top=True, bottom=False,
                       labeltop=True, labelbottom=False)

        # Rotate the tick labels and set their alignment.
        plt.setp(ax.get_xticklabels(), rotation=-30, ha="right",
                 rotation_mode="anchor")

        # Turn spines off and create white grid.
        for edge, spine in ax.spines.items():
            spine.set_visible(False)

        ax.set_xticks(np.arange(data.shape[1] + 1) - .5, minor=True)
        ax.set_yticks(np.arange(data.shape[0] + 1) - .5, minor=True)
        # ax.grid(which="minor", color="w", linestyle='-', linewidth=3)
        ax.tick_params(which="minor", bottom=False, left=False)

        return im, cbar

    @staticmethod
    def annotate_heatmap(im, data=None, valfmt="{x:.2f}",
                         textcolors=["black", "white"],
                         threshold=None, **textkw):
        """
        A function to annotate a heatmap.

        Arguments:
            im         : The AxesImage to be labeled.
        Optional arguments:
            data       : Data used to annotate. If None, the image's data is used.
            valfmt     : The format of the annotations inside the heatmap.
                         This should either use the string format method, e.g.
                         "$ {x:.2f}", or be a :class:`matplotlib.ticker.Formatter`.
            textcolors : A list or array of two color specifications. The first is
                         used for values below a threshold, the second for those
                         above.
            threshold  : Value in data units according to which the colors from
                         textcolors are applied. If None (the default) uses the
                         middle of the colormap as separation.

        Further arguments are passed on to the created text labels.
        """

        if not isinstance(data, (list, np.ndarray)):
            data = im.get_array()

        # Normalize the threshold to the images color range.
        if threshold is not None:
            threshold = im.norm(threshold)
        else:
            threshold = im.norm(data.max()) / 2.

        # Set default alignment to center, but allow it to be
        # overwritten by textkw.
        kw = dict(horizontalalignment="center",
                  verticalalignment="center")
        kw.update(textkw)

        # Get the formatter in case a string is supplied
        if isinstance(valfmt, str):
            valfmt = matplotlib.ticker.StrMethodFormatter(valfmt)

        # Loop over the data and create a `Text` for each "pixel".
        # Change the text's color depending on the data.
        texts = []
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                kw.update(color=textcolors[im.norm(data[i, j]) > threshold])
                text = im.axes.text(j, i, valfmt(data[i, j], None), **kw)
                texts.append(text)

        return texts

    # ============================== --------------------------------  ==============================
    #                                   Graphe operation

    @staticmethod
    def get_graph_list(folder: pathlib.Path):
        '''
        Store in an array all the output graphes of the algorithms
        :param folder:
        :return:
        '''
        graphe_list = []

        # For all graphe
        for x in folder.resolve().iterdir():
            if x.is_dir():

                tmp_to_write = {"name": x.name}
                curr_graphe_file = x / "graphe.py"

                try:
                    data = filesystem_lib.File_System.load_json(curr_graphe_file)
                    tmp_graphe = Graphe()
                    tmp_graphe.load_from_json(data)
                    tmp_to_write["graphe"] = tmp_graphe
                except Exception as e:
                    # We do not store something without graphe
                    tmp_to_write["graphe"] = None
                    continue

                curr_conf_file = x / "conf.txt"
                try:
                    data = filesystem_lib.File_System.load_json(curr_conf_file)
                    tmp_to_write["conf"] = data
                except Exception as e:
                    # We do not store something without graphe.
                    tmp_to_write["conf"] = None

                curr_stats_file = x / "stats.txt"
                try:
                    data = filesystem_lib.File_System.load_json(curr_stats_file)
                    tmp_to_write["stats"] = data
                except Exception as e:
                    # We do not store something without graphe.
                    tmp_to_write["stats"] = None

                    # Load each graphe
                graphe_list.append(tmp_to_write)

        return graphe_list

    @staticmethod
    def create_inclusion_matrix(folder: pathlib.Path):
        '''
        Create a inclusion (or kind of "similarity") matrix out of a folder with results from algorithms.
        :param folder:
        :return:
        '''
        # TODO : safe path in case it's not a Pathlib : is it necessary ?
        # folder = filesystem_lib.File_System.safe_path(folder)
        # output_folder = filesystem_lib.File_System.safe_path(output_folder)
        logger = logging.getLogger(__name__)
        logger.info(f"Creating inclusion matrix for {folder}")

        graphe_list = Graph_handler.get_graph_list(folder)

        # For all graphe A
        global_result = []
        for curr_graphe_a in graphe_list:
            logger.debug(f"Checking graphe {curr_graphe_a['name']} ...")

            tmp_result_graph_a = {}
            tmp_result_graph_a["source"] = curr_graphe_a['name']

            tmp_result_graph_b = []
            # For all graphe B
            for curr_graphe_b in graphe_list:
                logger.debug(f"Checking graphe {curr_graphe_a['name']} with {curr_graphe_b['name']}")

                # Evaluate each graphe A inclusion to each other graphe B
                tmp_mapping_dict = json_class.create_node_mapping(curr_graphe_a['graphe'], curr_graphe_b['graphe'])
                wrong_edge_list = json_class.is_graphe_included(curr_graphe_a['graphe'], tmp_mapping_dict, curr_graphe_b['graphe'])

                # Compute similarity based on inclusion (card(inclusion)/card(source))
                nb_edges = len(curr_graphe_a['graphe'].edges)
                curr_similarity = 1 - (len(wrong_edge_list) / nb_edges)

                # Store the similarity in an array
                tmp_dict = {}
                tmp_dict["compared_to"] = curr_graphe_b["name"]
                tmp_dict["similarity"] = curr_similarity
                tmp_result_graph_b.append(tmp_dict)

            # Store the similarity array as json
            # TODO : worth to sort it ? Would impact next computation
            tmp_result_graph_b = sorted(tmp_result_graph_b, key=lambda l: l["similarity"], reverse=True)
            tmp_result_graph_a["similar_to"] = tmp_result_graph_b
            global_result.append(tmp_result_graph_a)

        # Alphabetical order
        global_result = sorted(global_result, key=lambda l: l["source"])  # Sort by alphabetical order
        global_result = sorted(global_result, key=lambda l: len(l["source"]))  # And then by length

        return global_result

    @staticmethod
    def create_pair_matrix(folder: pathlib.Path, ground_truth_json: pathlib.Path):
        '''
        Create a quality matrix out of a folder with results from algorithms, by pairing result one-to-one.
        :param folder:
        :return:
        '''
        # TODO : safe path in case it's not a Pathlib : is it necessary ?
        # folder = filesystem_lib.File_System.safe_path(folder)
        # output_folder = filesystem_lib.File_System.safe_path(output_folder)
        logger = logging.getLogger(__name__)
        logger.info(f"Creating pair matrix for {folder}")

        graphe_list = Graph_handler.get_graph_list(folder)

        # Get grund_truth graphe
        ground_truth_graphe = Graphe()
        ground_truth_json_values = json_class.Json_handler.import_json(ground_truth_json.resolve())
        ground_truth_graphe.load_from_json(ground_truth_json_values)

        # For all graphe A
        global_result = []
        for curr_graphe_a in graphe_list:
            logger.debug(f"Loading graphe {curr_graphe_a['name']} ...")

            tmp_result_graph_a = {}
            tmp_result_graph_a["source"] = curr_graphe_a['name']

            tmp_result_graph_b = []
            # For all graphe B
            for curr_graphe_b in graphe_list:
                logger.debug(f"Merging graphe {curr_graphe_a['name']} with {curr_graphe_b['name']}")

                # Merging
                merged_graphe = json_class.merge_graphes(curr_graphe_a['graphe'], curr_graphe_b['graphe'])

                # Evaluating
                true_positive_rate = json_class.matching_graphe_percentage(merged_graphe, ground_truth_graphe)

                # Store the similarity in an array
                tmp_dict = {}
                tmp_dict["compared_to"] = curr_graphe_b['name']
                tmp_dict["similarity"] = true_positive_rate
                tmp_result_graph_b.append(tmp_dict)

            # Store the similarity array as json
            # TODO : worth to sort it ? Would impact next computation
            tmp_result_graph_b = sorted(tmp_result_graph_b, key=lambda l: l["similarity"], reverse=True)
            tmp_result_graph_a["similar_to"] = tmp_result_graph_b
            global_result.append(tmp_result_graph_a)

        # Alphabetical order
        global_result = sorted(global_result, key=lambda l: l["source"])  # Sort by alphabetical order
        global_result = sorted(global_result, key=lambda l: len(l["source"]))  # And then by length

        return global_result

    @staticmethod
    def generate_merged_pairs(input_folder: pathlib.Path, target_pair_folder: pathlib.Path):
        graphe_list = Graph_handler.get_graph_list(input_folder)

        logger = logging.getLogger(__name__)
        logger.info(f"Creating merged graphs for {input_folder} in {target_pair_folder}")

        tmp_conf = configuration.Default_configuration()
        tmp_stats = stats_lib.Stats_handler(conf=tmp_conf)

        # For all pair of graphes
        for curr_graphe_a in graphe_list:
            for curr_graphe_b in graphe_list:

                # Merge
                tmp_graphe_1 = Graphe()
                tmp_graphe_1.load_from_json(curr_graphe_a['graphe'])
                tmp_graphe_2 = Graphe()
                tmp_graphe_2.load_from_json(curr_graphe_b['graphe'])

                merged_graphe = json_class.merge_graphes(tmp_graphe_1, tmp_graphe_2)

                # Generate name
                new_name = curr_graphe_a["name"] + "_AND_" + curr_graphe_b['name']

                # Create folder
                future_folder_path = target_pair_folder / new_name
                future_folder_path.mkdir(parents=True, exist_ok=True)

                tmp_file_path = future_folder_path / "graphe.py"

                # Generate merged stats
                tmp_results = results.RESULTS()
                tmp_results.TIME_PER_PICTURE_MATCHING = curr_graphe_a['stats']["TIME_PER_PICTURE_MATCHING"] + curr_graphe_b['stats']["TIME_PER_PICTURE_MATCHING"]

                tmp_results.TIME_PER_PICTURE_PRE_COMPUTING = curr_graphe_a['stats']["TIME_PER_PICTURE_PRE_COMPUTING"] + curr_graphe_b['stats']["TIME_PER_PICTURE_PRE_COMPUTING"]

                tmp_results.TIME_TO_LOAD_PICTURES = curr_graphe_a['stats']["TIME_TO_LOAD_PICTURES"] + curr_graphe_b['stats']["TIME_TO_LOAD_PICTURES"]
                tmp_results.NB_PICTURE = max(curr_graphe_a['stats']["NB_PICTURE"], curr_graphe_b['stats']["NB_PICTURE"])

                # define where to write the stats
                tmp_conf.OUTPUT_DIR = future_folder_path
                tmp_stats.write_stats_to_folder(conf=tmp_conf, results=tmp_results)

                # Save file
                filesystem_lib.File_System.save_json(merged_graphe, file_path=tmp_file_path)
                '''
                f = open(str(tmp_file_path.resolve()), "w+")  # Overwrite and create if does not exist
                tmp_json = json.dumps(merged_graphe)
                f.write(tmp_json)
                f.close()
                '''

                # Copy the conf file
                copyfile(input_folder / curr_graphe_a['name'] / "conf.txt", future_folder_path / "conf_1.txt")
                copyfile(input_folder / curr_graphe_b['name'] / "conf.txt", future_folder_path / "conf_2.txt")

    @staticmethod
    def evaluate_graphs(target_pair_folder: pathlib.Path, ground_truth_json: pathlib.Path):
        graphe_list = Graph_handler.get_graph_list(target_pair_folder.resolve())

        logger = logging.getLogger(__name__)
        logger.info(f"Creating merged graphs for {target_pair_folder} in {target_pair_folder}")

        tmp_conf = configuration.Default_configuration()
        tmp_stats = stats_lib.Stats_handler(conf=tmp_conf)

        # Get grund_truth graphe
        ground_truth_graphe = Graphe()
        ground_truth_json_values = json_class.Json_handler.import_json(ground_truth_json.resolve())
        ground_truth_graphe.load_from_json(ground_truth_json_values)

        # For all pair of graphes
        for curr_graphe_a in graphe_list:
            # Evaluating
            true_positive_rate = json_class.matching_graphe_percentage(curr_graphe_a['graphe'], ground_truth_graphe)

            # define the results
            tmp_results = curr_graphe_a['stats']
            tmp_results["TRUE_POSITIVE_RATE"] = true_positive_rate

            # define where to write the stats
            tmp_conf.OUTPUT_DIR = (target_pair_folder / curr_graphe_a['name']).resolve()

            tmp_stats.write_stats_to_folder(conf=tmp_conf, results=tmp_results)

    @staticmethod
    def save_matrix_to_json(matrix, output_file: pathlib.Path):
        # Store the similarity array as picture
        # output_file = output_folder / "inclusion_matrix.json"
        filesystem_lib.File_System.save_json(matrix, file_path=output_file)
        '''
        f = open(str(output_file.resolve()), "w+")  # Overwrite and create if does not exist
        tmp_json = json.dumps(similarity_matrix)
        f.write(tmp_json)
        f.close()
        '''

        logger = logging.getLogger(__name__)
        logger.info("Matrix written")

        return output_file

    @staticmethod
    def inclusion_matrix_to_triple_array(inclusion_dict):
        '''
        Create a matrix out of a standard format
        Note : even if this is initially intended for inclusion score, this can be used for any format matching source/compared_to/similarity
        :param inclusion_dict:
        :return:
        '''
        ordo, absi, values = [], [], []

        for curr_source in inclusion_dict:
            # For the axis
            ordo.append(curr_source["source"])
            absi.append(curr_source["source"])

        for curr_source in ordo:
            tmp_row_values = []
            for curr_target in absi:
                tmp_similarity_list = Graph_handler.find_source_in_list(inclusion_dict, "source", curr_source)["similar_to"]
                value = Graph_handler.find_source_in_list(tmp_similarity_list, "compared_to", curr_target)["similarity"]
                tmp_row_values.append(value)
            values.append(tmp_row_values)

        return ordo, absi, values

    @staticmethod
    def find_source_in_list(list, tag, to_find):
        for x in list:
            if x[tag] == to_find:
                return x
        else:
            return None
