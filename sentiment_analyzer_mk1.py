from preprocessor_mk1 import TextPreprocessor
from textblob import TextBlob
from textblob.classifiers import NaiveBayesClassifier
from sklearn.decomposition import LatentDirichletAllocation
from collections import defaultdict
import pickle
import pymongo

class TextSentimentAnalysis(object):

    def __init__(self, classifier_filepath, processor):
        with open(classifier_filepath, 'rb') as f:
            self.classifier = pickle.load(f)
        self.processor = processor

    def _launch_mongo(self, db_name, coll_name):
        mc = pymongo.MongoClient(self.uri)
        db = mc[db_name]
        coll = db[coll_name]
        return coll

    def _create_blob(self, article):
        blob = TextBlob(article, self.classifier)
        return blob

    def _return_top_words(self, model, feature_names, n_top_words = 50):
        topic_dict = {}
        for topic_idx, topic in enumerate(model.components_):
            topic_top_n_words = set([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]])
            topic_dict[topic_idx] = topic_top_n_words

        return topic_dict

    def _whole_doc_sentiment(self, article):
        article_prob_dist = self.classifier.prob_classify(article)
        prediction = article_prob_dist.max()
        pred_prob = article_prob_dist.prob(prediction)

        return prediction, pred_prob

    def _sentiment_per_sentence(self, topic_dict, blob):
        sentiments_dict = defaultdict(lambda : defaultdict(list))
        for k, v in topic_dict.iteritems():
            for sentence in blob.sentences:
                sent_set = set(sentence.split())
                if len(v.intersection(sent_set)) > 2: #2 is an arbitrary number
                    sent_dist = self.classifier.prob_classify(sentence)
                    sent_pred = sent_dist.max()
                    sentiments_dict[k]['sentences'].append(sentence)
                    sentiments_dict[k]['predictions'].append(sent_pred)
            sentiments_dict[k]['topic_features'] = v

        return sentiments_dict

    def _lda_dim_reduction(self, vectorized_tokens, vectorizer):
        lda = LatentDirichletAllocation(n_components = 3, learning_method = 'batch').fit(vectorized_tokens)
        feature_names = vectorizer.get_feature_names()
        topic_dict = self._return_top_words(lda, feature_names)

        return topic_dict

    # --------- All private methods above this line -------

    def print_top_words(self, model, feature_names, n_top_words):
        for topic_idx, topic in enumerate(model.components_):
            message = "Topic #{}: ".format(topic_idx)
            message += " ".join([feature_names[i] for i in topic.argsort()[:-n_top_words - 1:-1]])
            print(message)

    def find_article_sentiment(self, article, vectorized_tokens, vectorizer):
        blob = self._create_blob(article)
        art_pred, art_prob = self._whole_doc_sentiment()
        topic_dict = self._lda_dim_reduction(vectorized_tokens, vectorizer)
        sentiments_dict = self._sentiment_per_sentence(topic_dict, blob)

        return art_pred, sentiments_dict

    #--------- TODO: NEED TO COMPLETE FUNCTIONS BELOW THIS LINE ------------
    def corpus_analytics(self, db_name, coll_name, uri = None):
        coll = self._launch_mongo(db_name, coll_name, uri)
        count = 0
        print 'Analyzing Articles and Storing in Mongo'
        for doc in coll.find():
            count += 1
            print 'Pass #{}'.format(count)
            doc_id = doc['_id']
            article = doc['article']
            cleaned = self.processor._correct_sentences(article)
            vectorizer, vectorized_tokens = self.processor.generate_vectors(cleaned, lemmatize = False)
            art_pred, sentiments_dict = self.find_article_sentiment(cleaned, vectorized_tokens, vectorizer)
            coll.find_one_and_update({'_id':doc_id}, {'$set':{'sentiment':sentiments_dict}})
        print 'COMPLETE'

    def cluster_by_topic_similarity(self, db_name, coll_name, uri = None):
        coll = self._launch_mongo(db_name, coll_name, uri)
        topics_list = []
        for doc in coll.find():
            doc_id = doc['_id']
            for k, v in doc['sentiments_dict'].iteritems():
                topics_list.append(v)
        vectorized = self.processor._vectorize(topics_list)
        # TODO: make clusters kmeans, Heirarchical clustering? set by min cluster size?






if __name__ == '__main__':
    db_name = 'news_articles'
    coll_name = 'article_text_data'
    uri = 'mongodb://root:TWV7Y1t7hS7P@localhost'
    prep = TextPreprocessor()
    prep.db_pipeline(db_name, coll_name, uri)
    filepath = '/home/bitnami/naivebayesclassifier.pkl'
    sentiment_analyzer = TextSentimentAnalysis(filepath, prep)
    sentiment_analyzer.corpus_analytics(db_name, coll_name, uri)



    article_text = prep.new_article('https://www.washingtonpost.com/local/virginia-politics/reeks-of-subtle-racism-tensions-after-black-candidate-left-off-fliers-in-virginia/2017/10/18/de74c47a-b425-11e7-a908-a3470754bbb9_story.html?utm_term=.2e8be491c0a3')
    vectorizer, vectorized_tokens = prep.generate_vectors(article_text, lemmatize = False)

    sentiment_analyzer = TextSentimentAnalysis(filepath)
    topics_dict = sentiment_analyzer._lda_dim_reduction(vectorized_tokens, vectorizer)

    article_pred, sentiments_dict = sentiment_analyzer.find_article_sentiment(vectorized_tokens, vectorizer)
    sentiments_dict
    prob_dist = sentiment_analyzer.classifier.prob_classify(article_text)
    pred = prob_dist.max()
    prob_dist.prob(pred)
