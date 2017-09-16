import logging

import generic_vector
import utils

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


class GenreTag(generic_vector.GenericTag):
    def __init__(self, genre):
        super(GenreTag, self).__init__(genre)
        self.combined_data = self.get_combined_data()
        self.time_utils = utils.TimestampUtils(self.combined_data)
        self.genre_data = self.get_combined_data_for_object()
        self.model_utils = utils.ModelUtils(self.genre_data)

    def get_combined_data(self):
        mltags = self.data_extractor.get_mltags_data()
        genome_tags = self.data_extractor.get_genome_tags_data()
        mlmovies = self.data_extractor.get_mlmovies_data()

        temp = mltags.merge(genome_tags, left_on="tagid", right_on="tagId", how="left")
        del temp['tagId']

        result = temp.merge(mlmovies, on="movieid", how="left")
        del result['userid']
        del result['moviename']
        del result['tagid']

        return result

    def get_combined_data_for_object(self):
        result = self.combined_data[self.combined_data['genres'].str.contains(self.object_id)]
        return result

    def get_weighted_tags_for_model(self, model):
        row_weights = []
        for index, row in self.genre_data.iterrows():
            movie_id = row['movieid']
            tag = row['tag']
            timestamp = row['timestamp']
            row_weight = self.time_utils.get_timestamp_value(timestamp) + self.get_model_value(movie_id, tag, model)
            row_weights.append(row_weight)

        self.genre_data.is_copy = False
        self.genre_data['row_weight'] = row_weights
        tag_group = self.genre_data.groupby(['tag'])
        result = {}
        for tag, df in tag_group:
            result[tag] = sum(df['row_weight'])

        return result

    def get_model_value(self, movie_id, tag_of_movie, model):
        if model == "tf":
            return self.model_utils.get_tf_value(movie_id, tag_of_movie) * 100
        elif model == "tfidf":
            return self.model_utils.get_tfidf_value(movie_id, tag_of_movie) * 100
        else:
            exit(1)


if __name__ == "__main__":
    obj = GenreTag("Thriller")
    print "TF-IDF values for genre : Thriller\n"
    result = obj.get_weighted_tags_for_model("tfidf")
    utils.sort_and_print_dictionary(result)
