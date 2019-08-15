from flask import Flask,render_template,request, redirect, url_for
from SPARQLWrapper import SPARQLWrapper, JSON
import hashlib


sparql = SPARQLWrapper("http://localhost:8890/sparql")
graph = "<http://localhost:8890/DAV/drugs>"
visited = set()
edges = set()
nodes = {}

app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = "static/ontologies"
# app.config['PLOTS_FOLDER'] = "static/ontologies/plots"
# app.config['JSON_FOLDER'] = "static/js"



# @app.route("/newConfirm",methods=['POST'])
# def newConfirm():
# 	id_ontology = (config_coll.find_one())['id_ontology']
# 	ontologia = {"id":id_ontology,"name":request.form['nome'],"description":request.form['descricao'],"file":"","image":"","qtd_classes":0,"qtd_properties":0,"qtd_evaluations":0,"classes":{},"properties":{}} 

# 	ontologia_file = request.files['ontologia']
# 	ext_ontologia = ontologia_file.filename.split(".")[1]
# 	ontologia_file_name = str(id_ontology)+"."+ext_ontologia
# 	ontologia_file_path = os.path.join(app.config['UPLOAD_FOLDER'],ontologia_file_name)
# 	ontologia_file.save(ontologia_file_path)
# 	ontologia["file"] = ontologia_file_path

# 	if "foto" in request.files and request.files['foto'].filename != '':
# 		#print(request.files['foto'].filename)
# 		foto_file = request.files['foto']
# 		ext_foto = foto_file.filename.split(".")[1]
# 		foto_file_name = str(id_ontology)+"."+ext_foto
# 		foto_file_path = os.path.join(app.config['UPLOAD_FOLDER'],foto_file_name)
# 		foto_file.save(foto_file_path)
# 		ontologia["image"] = foto_file_path

# 	g = ont.getGraph(ontologia_file_path,ext_ontologia)

# 	classes = ont.getClasses(g)
# 	properties = ont.getProperties(g)

# 	ontologia['classes'] = classes
# 	ontologia['qtd_classes'] = len(classes)
	
# 	ontologia["properties"] = properties
# 	ontologia['qtd_properties'] = len(properties)

# 	onto_coll.insert_one(ontologia)
# 	config_coll.update_many({},{'$set':{'id_ontology':id_ontology+1}})


# 	return redirect(url_for("menu"))
def getDatatypeProperties(uri):
	sparql.setQuery("""
	    SELECT DISTINCT ?p ?o FROM """+graph+""" WHERE{
			"""+uri+""" ?p ?o.
			FILTER(isLiteral(?o))
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	properties = {}
	for result in results["results"]["bindings"]:
		id_property = uri_to_hash(result["p"]["value"])

		if not id_property in properties:
			properties[id_property] = {'uri':result["p"]["value"],'values':[]}
		properties[id_property]['values'].append(result["o"]["value"])
	return properties

def getObjectProperties(uri):
	sparql.setQuery("""
	    SELECT DISTINCT ?p ?o FROM """+graph+""" WHERE{
			"""+uri+""" ?p ?o.
			FILTER(isIRI(?o) && regex(str(?p), "^(?!http://www.w3.org/2002/07/owl#).+") && regex(str(?o), "^(?!http://www.w3.org/2002/07/owl#).+"))
		}
	""")
	sparql.setReturnFormat(JSON)
	results = sparql.query().convert()
	neighbors = []
	for result in results["results"]["bindings"]:
		edges.add((uri_to_hash(uri),result["p"]["value"],uri_to_hash("<"+result["o"]["value"]+">"),result["p"]["value"].split("/")[-1].split("#")[-1].replace(">","")))
		neighbors.append("<"+result["o"]["value"]+">")
	return neighbors

def visit_node(uri,depth):
	if depth <= 0 or uri in visited:
		return
	visited.add(uri)
	id_uri = uri_to_hash(uri)
	nodes[id_uri] = {'uri':uri,'label':uri.split("/")[-1].replace(">",""),'properties':getDatatypeProperties(uri)}
	for neighbor in getObjectProperties(uri):
		visit_node(neighbor,depth-1)



def explore(uri):
	depth = 3
	visited.clear()
	edges.clear()
	visit_node(uri,depth)



@app.route("/")
def index():
	explore("<http://www.linkedmed.com.br/resource/drugs/consumidor/Medicamento/ACETILCISTEÍNA05.161.069%2F0001-10>")
	return render_template('index.html',nodes=nodes,edges=edges)


def uri_to_hash(uri):
	return hashlib.md5(str(uri).encode('utf-8')).hexdigest()

if __name__ == "__main__":
	#app.run(host='200.19.182.252')
	app.run(host='0.0.0.0')