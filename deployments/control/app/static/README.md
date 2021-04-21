Here you can find all the static files used to create the SPRAYai webui.

- `CSS` contains the compiled stylesheet files, have a look inside `sass` to see the code used to generate the custom stylesheets. Each element inside `custom_bulma.scss` customises something about the UI, from the page background image to the position of a button icon.
- `dependencies` contains addon style and JavaScript files. They are bundled locally as the SPRAYai system likely won't have an internet connection to retrieve them from a CDN.
- `fonts` contains the web fonts used within the UI.
- `img` contains images used throughout the UI and for favicons.
- `js` contains JavaScript code used to run the UI. As a primary objective was to consolidate as much code as possible (i.e. using Python where possible) there isn't much code here. Mainly it just provides the initial WebSocket connection to the backend, and generates the charts showing recent performance. All other JS is dynamically injected using Python.
