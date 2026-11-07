## start script 

python app.py


## setup

1) Install the standalone Termux:API companion app from F-Droid or GitHub (do not mix F-Droid and Play Store versions) 

2) Open Termux and install the corresponding system packages, Python, and dependencies
`pkg update && pkg upgrade -y`
`pkg install termux-api python -y`
`pip install flask`


problem to solve: when the screen sleeps, the app will be frozen :/
