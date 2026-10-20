# Tattoo Try-On

A browser AR app for previewing a tattoo on your skin before you get it.

- **Live camera** or **photo** background (front/back camera switch, freeze frame)
- Built-in flash designs, custom lettering (script, blackletter, typewriter), or upload your own image
- White backgrounds are removed from uploads automatically
- Drag to move, pinch to resize and rotate (mouse wheel / shift+wheel on desktop)
- **Wrap** bends the design around a limb; ink is multiplied into the skin so texture shows through
- Ink styles: stencil transfer, fresh black, healed (softer, blue-black), or original colors
- Save or share the result as a JPG

## Run it

It's a single `index.html` with no build step. The camera only works over `https://` or `localhost`:

```sh
cd tattoo-ar
python3 -m http.server 8000   # then open http://localhost:8000
```

To use it on your phone, host the folder on any static host with HTTPS (for example GitHub Pages: Settings → Pages → deploy from this branch, then open `/tattoo-ar/`).
