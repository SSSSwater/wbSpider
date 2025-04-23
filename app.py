from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def anl():
    return render_template('analysis.html')
@app.route('/intro')
def intro():
   return render_template('intro.html')
@app.route('/index')
def index():
   return render_template('index.html')


if __name__ == '__main__':
    app.run()