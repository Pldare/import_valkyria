# import_valkyria: A Blender Add-on for Valkyria Chronicles models

`import_valkyria` is a Blender 2.63+ add-on for importing MLX, HMD, ABR,
and MXE models from Valkyria Chronicles. The model files used by the
PlayStation 3 and PC versions of Valkyria Chronicles are the same, so both
versions are supported.

To use `import_valkyria`, you have to install it (once) and activate it (each
time you start Blender, or in your startup file).

## Installing and activating

To install, open Blender's User Preferences panel, click the Add-ons tab,
click the Install from File button, select import_valkyria-X.X.zip, and click
Install.

To activate, open Blender's User Preferences panel, click the Addons tab,
find "Import-Export: Valkyria Chronicles (.MLX, .HMD, .ABR, .MXE)", and click
its checkbox.

## Importing Models

Once `import_valkyria` is installed and activated, you can import a model by
clicking File, Import, Valkyria Chronicles (.MLX, .HMD, .ABR, .MXE), or by
pressing space, typing valk, and choosing it from the list.

## Splitting `DATA.CVM`

Model files are contained inside `DATA.CVM`.

To split `DATA.CVM` into usable files, use chrrox's `quickbms` script, which
you can download here:

http://forum.xentax.com/viewtopic.php?p=76717#p76717

## Known Issues

Blender 2.66 and 2.66a have a bug that causes some textures to be blank in the
viewport and in game mode, but not when rendering. Use 2.65a or 2.67+ instead.

Blender frequenty recalculates normal vectors, so there's not really a way to
use the normal vectors specified in the game.

Bones are a little bit weird because this was the best way I could think of to
get bones to correspond to the right vertex groups. Also, armature
relationships that exist in some models (such as between the body armature and
the head armature) are not supported.

Poses are disabled for now because I never finished this feature, but I wanted
to release a new version for other reasons.

## Changelog

### 2017-??-??: Version 0.7

* Added preliminary support for armature poses/animations.
    (Temporarily disabled.)
* Uploaded to github and added README.

### 2013-05-25: Version 0.6

* Added preliminary support for ABR models.
* Added preliminary support for MXE models.
* Added support for double textures. Normal map support is now broken.

### 2013-05-11: Version 0.5

* Renamed from hmdl_import to import_valkyria.
* Heavily refactored for encapsulation and extensibility.
* Handles bones differently, allowing fingertip articulation.
* Supports shape keys for facial expressions, etc.

### 2013-04-26: Version 0.4

* Preview release. Poorly coded and poorly documented.
* First release that works in Blender 2.63+
* Has preliminary support for bones.
* Has better support for materials, including normal maps and transparency.