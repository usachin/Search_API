from flask import Flask,  render_template, request, jsonify
import flask
import os
import sys
import base64
import json
import cv2
import wikipedia 
from flask_cors import CORS
try:
	from googlesearch import search 
except ImportError:
	print("No module named 'google' found")

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'content_type'
CORS(app)
cors = CORS(app,resources={r'/api/*':{"origins":"*"}})

import argparse
import io
# import os
from google.cloud import vision

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r"delta-generator-301608-432a1928693b.json"

def annotate(path):
    """Returns web annotations given the path to an image."""
    client = vision.ImageAnnotatorClient()

    if path.startswith('http') or path.startswith('gs:'):
        image = vision.Image()
        image.source.image_uri = path

    else:
        with io.open(path, 'rb') as image_file:
            content = image_file.read()

        image = vision.Image(content=content)

    web_detection = client.web_detection(image=image).web_detection

    return web_detection


def report(annotations):
    """Prints detected features in the provided web annotations."""
    results = {"best_guess_labels":[],"pages_with_matching_images":[], "full_matching_images": [], "partial_matching_images" :[], "web_entities": {"Score":[],"Description":[]}}
    if annotations.pages_with_matching_images:
        #print('\n{} Pages with matching images retrieved'.format(
        #    len(annotations.pages_with_matching_images)))

        for page in annotations.pages_with_matching_images:
            # print('Url   : {}'.format(page.url))
            results["pages_with_matching_images"].append(page.url)
    
    if annotations.best_guess_labels:
        for label in annotations.best_guess_labels:
            results["best_guess_labels"].append(label.label)

    if annotations.full_matching_images:
        # print('\n{} Full Matches found: '.format(
        #      len(annotations.full_matching_images)))

        for image in annotations.full_matching_images:
            # print('Url  : {}'.format(image.url))
            results["full_matching_images"].append(page.url)

    if annotations.partial_matching_images:
        # print('\n{} Partial Matches found: '.format(
        #       len(annotations.partial_matching_images)))

        for image in annotations.partial_matching_images:
            # print('Url  : {}'.format(image.url))
            results["partial_matching_images"].append(image.url)
    if annotations.web_entities:
        # print('\n{} Web entities found: '.format(
        #      len(annotations.web_entities)))

        for entity in annotations.web_entities:
            # print('Score      : {}'.format(entity.score))
            # print('Description: {}'.format(entity.description))
            results["web_entities"]["Score"].append(entity.score)
            results["web_entities"]["Description"].append(entity.description)
    return results

def double_query(search_for):
	query = search_for
	results = []
	for j in search(query, tld="co.in", num=10, stop=10, pause=2):
		results.append(j)
	return results

@app.route("/api/search/<search_for>", methods=['GET','POST'])
def google_search(search_for):
	query = search_for
	results = []
	json_result = {}
	for j in search(query, tld="co.in", num=1, stop=1, pause=2):
		results.append(j)
	json_result["search_result"] = [search_for, results]

	return jsonify(json_result)

@app.route("/api/<image_name>", methods=['GET','POST'])
def google_api_search(image_name):
	if request.method == 'GET':
		# add git path where you are uploading image in SSD server
		git_path ="https://raw.githubusercontent.com/JnaneshD/SSDimages/main/"
		file_path = git_path + image_name
		img_name = image_name.split(".")
		cls_name = ""
		if(len(img_name)>0):
			for i in img_name[0]:
				if(i.isalpha()):
					cls_name += i
		result = report(annotate(file_path))
		final_result = {}
		if(result == 503):
			final_result["service"] = "service unavailable"
			return jsonify(final_result)
		final_result = {}
		final_result["full_matching_images"] = result["full_matching_images"][:2]
		final_result["pages_with_matching_images"] = result["pages_with_matching_images"][:5]
		final_result["partial_matching_images"] = result["partial_matching_images"][:2]
		final_result["web_entities"] = {}
		final_result["web_entities"]["Description"] = []
		final_result["web_entities"]["Score"] = []
		final_result["web_entities"]["Description"] = result["web_entities"]["Description"][:5]
		final_result["web_entities"]["Score"] = result["web_entities"]["Score"][:5]
		final_result["best_guess_labels"] = result["best_guess_labels"]
		try:
			wiki_disc = wikipedia.summary(result["web_entities"]["Description"][0] +" " + result["best_guess_labels"][0] + " "+ cls_name  , sentences = 2)
			final_result["wiki"] = [wiki_disc] 
		except Exception as e:
			print(e)
			final_result["wiki"] = []
		
		
				
		return jsonify(final_result)

if __name__ == '__main__':
	app.run(host="0.0.0.0",debug=True, port=8000)
