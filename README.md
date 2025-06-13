# PyRT

**PyRT** is a simple-ish sample path tracer built using Python, OpenGL, and Dear ImGui.

It uses a built-in declarative DSL for scene descriptions, with scene files using *.pyrt* extension.

## Motivation

This project was made possible by the brilliant [Ray Tracing in One Weekend](https://raytracing.github.io/) book series!

**PyRT** was my first proper introduction to _GPU-based path tracing_, and it lacks many features of a _proper_ path tracer (e.g., it does not use any acceleration structure whatsoever) and boasts a codebase that _I am afraid of!_

Aka, this program needs a lot of stuff to be implemented, but I can't be bothered at this point.

## Features

- [x] Monte-Carlo path tracing.
- [x] Interactive GUI.
- [x] Custom domain-specific language for describing scenes.
- [x] Simple material system.
- [x] Object grouping.
- [x] FK positioning schema.
- [x] Configurable skybox.

## Launching/Requirements

I recommend using Python **>= 3.9**.

To launch the program, use the **start.bat** file. It'll:
- Automatically create a virtual environment if no is found.
- Change python environment from the global to PyRT.
- Download all required packages.
- Launch the program.

In the specified order.

## Controls

### Camera

Camera movement is controlled via WASD, Space and Left Control.

Camera rotation is controlled via moving the mouse while holding down the middle mouse button.

### Render settings

Render settings (Accumulate frames, sample and reflection count) are located under **Settings/Render**. PostFX settings are located under **Settings/postFX** Changes will be reset on restart, to fix that - edit **settings.toml** in the root directiory.

### Scene and skybox loading

Scenes and skyboxes can be located under **File/Open scene** and **File/Open skybox**. *Note - only .pyrt files are supported for scene loading, and for skyboxes - .png and .jpg*

### GUI hiding

GUI can be hidden by pressing **m**.

*Known issue - GUI can be hidden while typing in textboxes*
