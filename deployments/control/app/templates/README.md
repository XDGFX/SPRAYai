Here are the 'templates' used by Python Flask to generate the HTML which is viewed by the user through their web browser.

- `index.html`, `settings.html`, and `login.html` all correspond to different pages within the UI.
- `test.html` was just used for development of the SPRAYai stylesheet, it's not actually used in the UI.

Any curly brackets (either `{{  }}` or `{%  %}`) correspond to some template injection, where Python Flask will generate HTML in its place automatically when the page is requested, allowing updated Python variables or other code to be adapted to the current state.
