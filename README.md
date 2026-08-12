# StreamController-Plugins
This repo contains links to all assets of [StreamController](https://github.com/Core447/StreamController).

## Submitting a page

`Pages.json` does not point at whole repositories like the other files, but at single
`.scpage` files inside them. That way a plugin repository can ship pages for its own
actions without having to be a page repository.

1. Export the page from StreamController: page manager → ⋮ → *Export page*. The resulting
   `.scpage` already contains every image the page uses and the list of plugins and icon
   packs it needs, so nothing else has to be shipped with it.
2. Commit the `.scpage`, a thumbnail and a manifest to a public repository. The manifest
   has to sit next to the page and carry the same name, so `now-playing.scpage` needs a
   `now-playing.manifest.json`:

   ```json
   {
       "id": "com_core447_MediaPlugin_NowPlaying",
       "name": "Now Playing",
       "version": "1.0.0",
       "thumbnail": "thumbnails/now-playing.png",
       "descriptions":       { "en_US": "Shows the current track with play/pause and skip." },
       "short-descriptions": { "en_US": "Media controls" },
       "minimum-app-version": "1.5.0",
       "app-version": "1.5.0-beta.16",
       "tags": ["media"],
       "deck": { "rows": 3, "columns": 5, "dials": 0, "touchscreen": false }
   }
   ```

   `id` has to be unique across the whole store - it is what links an installed page back
   to its entry here. `thumbnail` is relative to the folder the manifest is in. `deck` is
   optional and only shown to the user, pages are never hidden because of it.
3. Add the entry to `Pages.json` and open a pull request:

   ```json
   [
       {
           "url": "https://github.com/StreamController/MediaPlugin",
           "pages": [
               {
                   "path": "store-pages/now-playing.scpage",
                   "commit": "f4be6cb3db50657b7d4a2f6ed9eecf415c382035"
               }
           ]
       }
   ]
   ```

   Every page is pinned to its own commit, so adding a page does not move the others.

Before opening the pull request you can check your entry with:

```sh
python3 scripts/validate_pages.py
```
