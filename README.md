# Parametric Glasses

Process:
1. Takes in a photo of a person's head and outputs the recommended bridge width and frame width of spectacles. (done)
    1. Take a picture of your head, try to be as parallel to the camera hole as possible
    2. Run the script
    3. Produces two numbers - recommmended bridge width and frame width.
2. Takes in a photo of a lens and outputs a 2D file. (done)
    1. Take a picture of your lens against the calibration background in \examples
    2. Run the script
    3. Produces a 2D DXF file 
3. Produces a STL file. (kiv)


## Installation

```
conda create --name mediapipe_iris python=3.7
conda activate mediapipe_iris
pip install -r requirements.txt
```

## Execution

python3 face-landmarks.py --image_filename [input_file]
python3 lens.py [input_file] [output_file]


# Notes
- Designed for adult heads
- Returns default bridge width and frame width parameters if out of human range.
- Lens CV may not work for clear lenses

# Credits

Thanks to https://github.com/Morris88826/MediaPipe_Iris
