with open("gh-address-cr/scripts/cr_loop.py", "r") as f:
    content = f.read()

content = content.replace("import shlex\nimport subprocess\nimport sys\nimport uuid\nimport shlex", "import shlex\nimport subprocess\nimport sys\nimport uuid")

with open("gh-address-cr/scripts/cr_loop.py", "w") as f:
    f.write(content)
