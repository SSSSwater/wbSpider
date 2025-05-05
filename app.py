from flask import Flask, render_template, request, jsonify
from flask_restful import Resource, Api, reqparse

app = Flask(__name__)
api = Api(app)

@app.route('/')
def anl():
    return render_template('analysis.html')

@app.route('/intro')
def intro():
   return render_template('intro.html')

@app.route('/index')
def index():
   return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

parser = reqparse.RequestParser()
parser.add_argument('userId', type=int, help='Rate to charge for this resource')

class UserInfo(Resource):
    def get(self):
        args = parser.parse_args()
        print(args)

api.add_resource(UserInfo, '/anl/user')
# @app.route('/anl/user', methods=["GET","POST"])
# def anl_user():
#     json_value = request.get_json()
#     print(json_value['input'])
# # 发送数据
#     info = dict()
#     info["status"] = "success"
#     info["page"] = "/test/lyshark"
#     return jsonify(info)

if __name__ == '__main__':
    app.run(debug=True)