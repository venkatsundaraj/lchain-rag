corpus = {'corpus_id': Value('int64'), 'doc_id': Value('string'), 'markdown': Value('string'), 'page_number_in_doc': Value('int64')}

queries = {'query_id': Value('int64'), 'query':Value('string'), 'language': Value('string'), 'query_types': List(Value('string')), 'query_format': Value('string'), 'content_type': List(Value('string')), 'raw_answers': List(Value('string')), 'query_generator': Value('string'), 'query_generation_pipeline': Value('string'), 'source_type': Value('string'), 'query_type_for_generation': Value('string'), 'answer': Value('string')}

qrels = {'query_id': Value('int64'), 'corpus_id': Value('int64'), 'score': Value('int64'), 'content_type': List(Value('string')), 'bounding_boxes': List({'annotator': Value('int64'), 'x1': Value('int64'), 'x2': Value('int64'), 'y1': Value('int64'), 'y2': Value('int64')})}

docs = {'file_name': Value('string'), 'doc_id': Value('string'), 'url': Value('string'), 'doc_type': Value('string'), 'doc_language': Value('string'), 'doc_year': Value('int64'), 'visual_types': List(Value('string')), 'page_number': Value('int64'), 'license': Value('string')}
