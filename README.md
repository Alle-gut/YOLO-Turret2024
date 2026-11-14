# YOLO-Turret2024
Destitute version of other AI controlled turret people built in 2024 because I did not get any help in research funding (The Jetson was lent by lab). Lucky for you, you can replicate it because how cheap it is!

Note in problems:
1. Memory leak in GUI because forgot to add cleanup
2. NVIDIA Jetson 4GB is NOT GOOD ENOUGH despite their TOPSmaxxing simply because 4GB RAM is too small for RAM, and the latency (601ms) cannot be compared to laptop RTX3050
3. Using vanilla IMX219 it have limited resolution and the leak prevented further processing for increased accuracy

Success:
1. It worked despite unreliably in completely different place where the training data was taken
2. The turret can track the target accurately if given... chance to self correct
3. Despite costing 30$ + Lent Jetson the program and the turret itself worked as intended considering the funding and technical limitations

Go ahead and replicate and improve it, vibe code on it or make it your research paper on improvement n such.
