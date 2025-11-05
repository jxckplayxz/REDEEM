from flask import Flask, Response

app = Flask(__name__)

html_page = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Site Down</title>

<style>
    body {
        margin: 0;
        padding: 0;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        background: linear-gradient(-45deg, #000000, #111111, #050505, #0a0a0a);
        background-size: 400% 400%;
        animation: gradientMove 10s ease infinite;
        font-family: Arial, sans-serif;
        color: white;
        overflow: hidden;
    }

    @keyframes gradientMove {
        0% {background-position: 0% 50%;}
        50% {background-position: 100% 50%;}
        100% {background-position: 0% 50%;}
    }

    .overlay {
        width: 70%;
        max-width: 600px;
        padding: 40px;
        text-align: center;
        background: rgba(0,0,0,0.6);
        backdrop-filter: blur(10px);
        border-radius: 0px;
        animation: roundedFade 1.8s ease forwards;
        border: 1px solid rgba(255,255,255,0.1);
    }

    @keyframes roundedFade {
        0%   {transform: scale(.9); opacity: 0; border-radius: 0px;}
        60%  {opacity: 1;}
        100% {transform: scale(1); border-radius: 30px;}
    }

    h1 {
        font-size: 2rem;
        margin: 0;
    }
    p {
        opacity: .7;
        margin-top: 8px;
    }
</style>
</head>
<body>

<div class="overlay">
    <h1>Site Down</h1>
    <p>Owner <strong>@evarge (Alex)</strong> shut it down</p>
</div>

</body>
</html>
"""

@app.route("/")
def down():
    return Response(html_page, mimetype="text/html")

if __name__ == "__main__":
    app.run(debug=True)