#1/bin/bash

IN=favicon.svg

function svg2ico {
  basename=${1%.svg}
  /Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=16 --export-height=16 --export-filename="$basename_16.png" "$1"
  /Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=32 --export-height=32 --export-filename="$basename_32.png" "$1"
  /Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=48 --export-height=48 --export-filename="$basename_48.png" "$1"
  /Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=96 --export-height=96 --export-filename="$basename_96.png" "$1"
  magick convert -verbose $basename_16.png $basename_32.png $basename_48.png $basename_96.png $basename.ico

}

svg2ico "${IN}"

/Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=96 --export-height=96 --export-filename=favicon-96x96.png ./${IN}
/Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=192 --export-height=192 --export-filename=web-app-manifest-192x192.png ./${IN}
/Applications/Inkscape.app/Contents/MacOS/inkscape --export-type=png --export-width=512 --export-height=512 --export-filename=web-app-manifest-512x512.png ./${IN}
