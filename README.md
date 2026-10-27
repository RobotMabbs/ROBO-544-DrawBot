# DrawBot 
To create the python environment with everything you need run:
```
pip install -r requirements.txt
```
To turn the image into a vector (and a path of x,y points) run:
```
python .\image_to_vector.py image.png --step=25 --save="saved.gif"
```
Using a bigger step will make the animation faster, and you can save the animation to a gif. Or leave as default for the animation to play in a pop-up. 