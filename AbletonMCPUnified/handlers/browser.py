"""Browser command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class BrowserHandlers(object):

    def _browse_path(self, path_list):
        """Navigate browser by path list e.g. ['Sounds', 'Bass', 'Sub Bass']"""
        try:
            app = self.application()
            browser = app.browser

            # Map category names to browser attributes (case-insensitive)
            category_map = {
                "instruments": browser.instruments,
                "sounds": browser.sounds,
                "drums": browser.drums,
                "audio_effects": browser.audio_effects,
                "midi_effects": browser.midi_effects,
            }

            # Add samples and packs if available
            if hasattr(browser, 'samples'):
                category_map["samples"] = browser.samples
            if hasattr(browser, 'packs'):
                category_map["packs"] = browser.packs

            if not path_list:
                # Return available categories
                return {
                    "path": [],
                    "available_categories": list(category_map.keys()),
                    "items": []
                }

            # Get starting category (normalize to lowercase with underscores)
            category = path_list[0].lower().replace(" ", "_")
            if category not in category_map:
                return {
                    "error": "Unknown category: {0}".format(category),
                    "available_categories": list(category_map.keys())
                }

            current = category_map[category]

            # Navigate through remaining path parts
            for i in range(1, len(path_list)):
                part = path_list[i]
                found = False
                if hasattr(current, 'children'):
                    for child in current.children:
                        if child.name.lower() == part.lower():
                            current = child
                            found = True
                            break
                if not found:
                    return {
                        "error": "Path part '{0}' not found".format(part),
                        "path": path_list[:i]
                    }

            # Return children of current item
            items = []
            if hasattr(current, 'children'):
                for child in current.children:
                    items.append({
                        "name": child.name,
                        "is_folder": child.is_folder if hasattr(child, 'is_folder') else False,
                        "is_device": child.is_device if hasattr(child, 'is_device') else False,
                        "is_loadable": child.is_loadable if hasattr(child, 'is_loadable') else False,
                        "uri": child.uri if hasattr(child, 'uri') else None
                    })

            return {
                "path": path_list,
                "items": items,
                "item_count": len(items)
            }
        except Exception as e:
            self.log_message("Error browsing path: " + str(e))
            raise
    def _get_browser_children(self, uri):
        """Get children of browser item by URI"""
        try:
            app = self.application()
            browser = app.browser

            # Find item by URI
            item = self._find_browser_item_by_uri(browser, uri)
            if not item:
                return {"error": "Item not found: {0}".format(uri)}

            children = []
            if hasattr(item, 'children'):
                for child in item.children:
                    children.append({
                        "name": child.name,
                        "is_folder": child.is_folder if hasattr(child, 'is_folder') else False,
                        "is_device": child.is_device if hasattr(child, 'is_device') else False,
                        "is_loadable": child.is_loadable if hasattr(child, 'is_loadable') else False,
                        "uri": child.uri if hasattr(child, 'uri') else None
                    })

            return {
                "uri": uri,
                "name": item.name if hasattr(item, 'name') else "Unknown",
                "children": children,
                "child_count": len(children)
            }
        except Exception as e:
            self.log_message("Error getting browser children: " + str(e))
            raise
    def _search_browser(self, query, category="all"):
        """Search browser for items matching query"""
        try:
            app = self.application()
            browser = app.browser

            results = []
            query_lower = query.lower()

            # Determine which categories to search
            categories_to_search = []
            if category == "all":
                categories_to_search = [
                    ("instruments", browser.instruments),
                    ("sounds", browser.sounds),
                    ("drums", browser.drums),
                    ("audio_effects", browser.audio_effects),
                    ("midi_effects", browser.midi_effects)
                ]
            elif category == "instruments":
                categories_to_search = [("instruments", browser.instruments)]
            elif category == "sounds":
                categories_to_search = [("sounds", browser.sounds)]
            elif category == "drums":
                categories_to_search = [("drums", browser.drums)]
            elif category == "audio_effects":
                categories_to_search = [("audio_effects", browser.audio_effects)]
            elif category == "midi_effects":
                categories_to_search = [("midi_effects", browser.midi_effects)]
            else:
                return {"error": "Unknown category: {0}".format(category)}

            def search_recursive(item, cat_name, depth=0):
                if depth > 4:  # Limit depth for performance
                    return
                if len(results) >= 50:  # Limit results
                    return

                # Check if item name matches query
                if hasattr(item, 'name') and query_lower in item.name.lower():
                    is_loadable = item.is_loadable if hasattr(item, 'is_loadable') else False
                    results.append({
                        "name": item.name,
                        "category": cat_name,
                        "uri": item.uri if hasattr(item, 'uri') else None,
                        "is_loadable": is_loadable,
                        "is_device": item.is_device if hasattr(item, 'is_device') else False
                    })

                # Recurse into children
                if hasattr(item, 'children') and (item.is_folder if hasattr(item, 'is_folder') else True):
                    for child in item.children:
                        search_recursive(child, cat_name, depth + 1)
                        if len(results) >= 50:
                            break

            for cat_name, cat_item in categories_to_search:
                if hasattr(cat_item, 'children'):
                    for child in cat_item.children:
                        search_recursive(child, cat_name)
                        if len(results) >= 50:
                            break

            return {
                "query": query,
                "category": category,
                "results": results,
                "result_count": len(results)
            }
        except Exception as e:
            self.log_message("Error searching browser: " + str(e))
            raise
    def _load_instrument_or_effect(self, track_index, uri):
        """Load an instrument or effect onto a track by URI"""
        try:
            track = self._validate_track_index(track_index)

            app = self.application()
            browser = app.browser

            # Find the browser item by URI
            item = self._find_browser_item_by_uri(browser, uri)

            if not item:
                return {"error": "Browser item not found: {0}".format(uri)}

            if not (item.is_loadable if hasattr(item, 'is_loadable') else False):
                return {"error": "Item is not loadable: {0}".format(item.name)}

            # Select the track so the item loads onto it
            self._song.view.selected_track = track

            # Load the item
            browser.load_item(item)

            return {
                "loaded": True,
                "item_name": item.name,
                "track_index": track_index,
                "track_name": track.name,
                "uri": uri
            }
        except Exception as e:
            self.log_message("Error loading instrument/effect: " + str(e))
            raise
    def _load_browser_item_to_return(self, return_index, item_uri):
        """Load a browser item onto a return track"""
        try:
            return_track = self._validate_return_track_index(return_index)

            app = self.application()
            browser = app.browser

            # Find the browser item by URI
            item = self._find_browser_item_by_uri(browser, item_uri)

            if not item:
                return {"error": "Browser item not found: {0}".format(item_uri)}

            if not (item.is_loadable if hasattr(item, 'is_loadable') else False):
                return {"error": "Item is not loadable: {0}".format(item.name)}

            # Select the return track
            self._song.view.selected_track = return_track

            # Load the item
            browser.load_item(item)

            return {
                "loaded": True,
                "item_name": item.name,
                "return_index": return_index,
                "return_track_name": return_track.name,
                "uri": item_uri
            }
        except Exception as e:
            self.log_message("Error loading item to return track: " + str(e))
            raise
    def _load_browser_item(self, track_index, item_uri):
        """Load a browser item onto a track by its URI"""
        try:
            if track_index < 0 or track_index >= len(self._song.tracks):
                raise IndexError("Track index out of range")
            
            track = self._song.tracks[track_index]
            
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            
            # Find the browser item by URI
            item = self._find_browser_item_by_uri(app.browser, item_uri)
            
            if not item:
                raise ValueError("Browser item with URI '{0}' not found".format(item_uri))
            
            # Select the track
            self._song.view.selected_track = track
            
            # Load the item
            app.browser.load_item(item)
            
            result = {
                "loaded": True,
                "item_name": item.name,
                "track_name": track.name,
                "uri": item_uri
            }
            return result
        except Exception as e:
            self.log_message("Error loading browser item: {0}".format(str(e)))
            self.log_message(traceback.format_exc())
            raise
    def _find_browser_item_by_uri(self, browser_or_item, uri, max_depth=10, current_depth=0):
        """Find a browser item by its URI"""
        try:
            # Check if this is the item we're looking for
            if hasattr(browser_or_item, 'uri') and browser_or_item.uri == uri:
                return browser_or_item
            
            # Stop recursion if we've reached max depth
            if current_depth >= max_depth:
                return None
            
            # Check if this is a browser with root categories
            if hasattr(browser_or_item, 'instruments'):
                # Check all main categories
                categories = [
                    browser_or_item.instruments,
                    browser_or_item.sounds,
                    browser_or_item.drums,
                    browser_or_item.audio_effects,
                    browser_or_item.midi_effects
                ]
                
                for category in categories:
                    item = self._find_browser_item_by_uri(category, uri, max_depth, current_depth + 1)
                    if item:
                        return item
                
                return None
            
            # Check if this item has children
            if hasattr(browser_or_item, 'children') and browser_or_item.children:
                for child in browser_or_item.children:
                    item = self._find_browser_item_by_uri(child, uri, max_depth, current_depth + 1)
                    if item:
                        return item
            
            return None
        except Exception as e:
            self.log_message("Error finding browser item by URI: {0}".format(str(e)))
            return None
    def _normalize_browser_category_name(self, category_name):
        """Normalize browser category names for robust matching."""
        try:
            normalized = (category_name or "").strip().lower()
            normalized = normalized.replace("-", "_").replace(" ", "_")
            while "__" in normalized:
                normalized = normalized.replace("__", "_")
            normalized = normalized.strip("_")

            # Canonical category aliases
            alias_map = {
                "instrument": "instruments",
                "sound": "sounds",
                "drum": "drums",
                "audioeffects": "audio_effects",
                "audio_fx": "audio_effects",
                "audiofx": "audio_effects",
                "midieffects": "midi_effects",
                "midi_fx": "midi_effects",
                "midifx": "midi_effects",
                "plugin": "plugins",
                "vst": "plugins",
                "vst2": "plugins",
                "vst3": "plugins",
                "au": "plugins",
            }

            if normalized in alias_map:
                return alias_map[normalized]

            compact = normalized.replace("_", "")
            if compact in alias_map:
                return alias_map[compact]

            return normalized
        except Exception:
            return (category_name or "").strip().lower()
    def _split_browser_path(self, path):
        """Split a browser path into normalized path parts."""
        if not path:
            return []
        return [part.strip() for part in path.split("/") if part and part.strip()]
    def _resolve_browser_root_category(self, browser, root_category, browser_attrs=None):
        """Resolve a root browser category to the corresponding browser item."""
        normalized_root = self._normalize_browser_category_name(root_category)

        standard_roots = {
            "instruments": "instruments",
            "sounds": "sounds",
            "drums": "drums",
            "audio_effects": "audio_effects",
            "midi_effects": "midi_effects",
            "plugins": "plugins",
        }

        attr_name = standard_roots.get(normalized_root)
        if attr_name and hasattr(browser, attr_name):
            return getattr(browser, attr_name), attr_name

        attrs = browser_attrs if browser_attrs is not None else [a for a in dir(browser) if not a.startswith('_')]
        for attr in attrs:
            if self._normalize_browser_category_name(attr) == normalized_root:
                try:
                    return getattr(browser, attr), attr
                except Exception as e:
                    self.log_message("Error accessing browser attribute {0}: {1}".format(attr, str(e)))

        return None, normalized_root
    def _get_browser_item(self, uri, path):
        """Get a browser item by URI or path"""
        try:
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")
                
            result = {
                "uri": uri,
                "path": path,
                "found": False
            }
            
            # Try to find by URI first if provided
            if uri:
                item = self._find_browser_item_by_uri(app.browser, uri)
                if item:
                    result["found"] = True
                    result["item"] = {
                        "name": item.name,
                        "is_folder": item.is_folder,
                        "is_device": item.is_device,
                        "is_loadable": item.is_loadable,
                        "uri": item.uri
                    }
                    return result
            
            # If URI not provided or not found, try by path
            if path:
                # Parse the path and navigate to the specified item
                path_parts = self._split_browser_path(path)
                if not path_parts:
                    result["error"] = "Invalid path"
                    return result
                
                # Determine the root based on the first part
                current_item, resolved_attr = self._resolve_browser_root_category(app.browser, path_parts[0])
                if current_item is None:
                    # Default to instruments if not specified
                    current_item = app.browser.instruments
                    # Don't skip the first part in this case
                    path_parts = ["instruments"] + path_parts
                elif resolved_attr != "instruments":
                    # Keep path parts aligned with resolved root
                    path_parts[0] = resolved_attr
                
                # Navigate through the path
                for i in range(1, len(path_parts)):
                    part = path_parts[i]
                    if not part:  # Skip empty parts
                        continue
                    
                    found = False
                    for child in current_item.children:
                        if child.name.lower() == part.lower():
                            current_item = child
                            found = True
                            break
                    
                    if not found:
                        result["error"] = "Path part '{0}' not found".format(part)
                        return result
                
                # Found the item
                result["found"] = True
                result["item"] = {
                    "name": current_item.name,
                    "is_folder": current_item.is_folder,
                    "is_device": current_item.is_device,
                    "is_loadable": current_item.is_loadable,
                    "uri": current_item.uri
                }
            
            return result
        except Exception as e:
            self.log_message("Error getting browser item: " + str(e))
            self.log_message(traceback.format_exc())
            raise   
    def get_browser_tree(self, category_type="all"):
        """
        Get a simplified tree of browser categories.
        
        Args:
            category_type: Type of categories to get ('all', 'instruments', 'sounds', etc.)
            
        Returns:
            Dictionary with the browser tree structure
        """
        try:
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")
                
            # Check if browser is available
            if not hasattr(app, 'browser') or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")
            
            # Log available browser attributes to help diagnose issues
            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith('_')]
            self.log_message("Available browser attributes: {0}".format(browser_attrs))
            
            result = {
                "type": category_type,
                "categories": [],
                "available_categories": browser_attrs
            }
            
            # Helper function to process a browser item and its children
            def process_item(item, depth=0):
                if not item:
                    return None
                
                result = {
                    "name": item.name if hasattr(item, 'name') else "Unknown",
                    "is_folder": hasattr(item, 'children') and bool(item.children),
                    "is_device": hasattr(item, 'is_device') and item.is_device,
                    "is_loadable": hasattr(item, 'is_loadable') and item.is_loadable,
                    "uri": item.uri if hasattr(item, 'uri') else None,
                    "children": []
                }
                
                
                return result
            
            # Process based on category type and available attributes
            if (category_type == "all" or category_type == "instruments") and hasattr(app.browser, 'instruments'):
                try:
                    instruments = process_item(app.browser.instruments)
                    if instruments:
                        instruments["name"] = "Instruments"  # Ensure consistent naming
                        result["categories"].append(instruments)
                except Exception as e:
                    self.log_message("Error processing instruments: {0}".format(str(e)))
            
            if (category_type == "all" or category_type == "sounds") and hasattr(app.browser, 'sounds'):
                try:
                    sounds = process_item(app.browser.sounds)
                    if sounds:
                        sounds["name"] = "Sounds"  # Ensure consistent naming
                        result["categories"].append(sounds)
                except Exception as e:
                    self.log_message("Error processing sounds: {0}".format(str(e)))
            
            if (category_type == "all" or category_type == "drums") and hasattr(app.browser, 'drums'):
                try:
                    drums = process_item(app.browser.drums)
                    if drums:
                        drums["name"] = "Drums"  # Ensure consistent naming
                        result["categories"].append(drums)
                except Exception as e:
                    self.log_message("Error processing drums: {0}".format(str(e)))
            
            if (category_type == "all" or category_type == "audio_effects") and hasattr(app.browser, 'audio_effects'):
                try:
                    audio_effects = process_item(app.browser.audio_effects)
                    if audio_effects:
                        audio_effects["name"] = "Audio Effects"  # Ensure consistent naming
                        result["categories"].append(audio_effects)
                except Exception as e:
                    self.log_message("Error processing audio_effects: {0}".format(str(e)))
            
            if (category_type == "all" or category_type == "midi_effects") and hasattr(app.browser, 'midi_effects'):
                try:
                    midi_effects = process_item(app.browser.midi_effects)
                    if midi_effects:
                        midi_effects["name"] = "MIDI Effects"
                        result["categories"].append(midi_effects)
                except Exception as e:
                    self.log_message("Error processing midi_effects: {0}".format(str(e)))
            
            # Try to process other potentially available categories
            for attr in browser_attrs:
                if attr not in ['instruments', 'sounds', 'drums', 'audio_effects', 'midi_effects'] and \
                   (category_type == "all" or category_type == attr):
                    try:
                        item = getattr(app.browser, attr)
                        if hasattr(item, 'children') or hasattr(item, 'name'):
                            category = process_item(item)
                            if category:
                                category["name"] = attr.capitalize()
                                result["categories"].append(category)
                    except Exception as e:
                        self.log_message("Error processing {0}: {1}".format(attr, str(e)))
            
            self.log_message("Browser tree generated for {0} with {1} root categories".format(
                category_type, len(result['categories'])))
            return result
            
        except Exception as e:
            self.log_message("Error getting browser tree: {0}".format(str(e)))
            self.log_message(traceback.format_exc())
            raise
    def get_browser_items_at_path(self, path):
        """
        Get browser items at a specific path.
        
        Args:
            path: Path in the format "category/folder/subfolder"
                 where category is one of: instruments, sounds, drums, audio_effects, midi_effects
                 or any other available browser category
                 
        Returns:
            Dictionary with items at the specified path
        """
        try:
            # Access the application's browser instance instead of creating a new one
            app = self.application()
            if not app:
                raise RuntimeError("Could not access Live application")
                
            # Check if browser is available
            if not hasattr(app, 'browser') or app.browser is None:
                raise RuntimeError("Browser is not available in the Live application")
            
            # Log available browser attributes to help diagnose issues
            browser_attrs = [attr for attr in dir(app.browser) if not attr.startswith('_')]
            self.log_message("Available browser attributes: {0}".format(browser_attrs))
                
            # Parse the path
            path_parts = self._split_browser_path(path)
            if not path_parts:
                raise ValueError("Invalid path")
            
            # Determine the root category
            root_category = path_parts[0]
            current_item, resolved_root = self._resolve_browser_root_category(
                app.browser, root_category, browser_attrs
            )
            if current_item is None:
                # If we still haven't found the category, return available categories
                return {
                    "path": path,
                    "error": "Unknown or unavailable category: {0}".format(
                        self._normalize_browser_category_name(root_category)
                    ),
                    "available_categories": browser_attrs,
                    "items": []
                }

            # Keep path canonicalized to resolved root category
            path_parts[0] = resolved_root
            
            # Navigate through the path
            for i in range(1, len(path_parts)):
                part = path_parts[i]
                if not part:  # Skip empty parts
                    continue
                
                if not hasattr(current_item, 'children'):
                    return {
                        "path": path,
                        "error": "Item at '{0}' has no children".format('/'.join(path_parts[:i])),
                        "items": []
                    }
                
                found = False
                for child in current_item.children:
                    if hasattr(child, 'name') and child.name.lower() == part.lower():
                        current_item = child
                        found = True
                        break
                
                if not found:
                    return {
                        "path": path,
                        "error": "Path part '{0}' not found".format(part),
                        "items": []
                    }
            
            # Get items at the current path
            items = []
            if hasattr(current_item, 'children'):
                for child in current_item.children:
                    item_info = {
                        "name": child.name if hasattr(child, 'name') else "Unknown",
                        "is_folder": hasattr(child, 'children') and bool(child.children),
                        "is_device": hasattr(child, 'is_device') and child.is_device,
                        "is_loadable": hasattr(child, 'is_loadable') and child.is_loadable,
                        "uri": child.uri if hasattr(child, 'uri') else None
                    }
                    items.append(item_info)
            
            result = {
                "path": path,
                "name": current_item.name if hasattr(current_item, 'name') else "Unknown",
                "uri": current_item.uri if hasattr(current_item, 'uri') else None,
                "is_folder": hasattr(current_item, 'children') and bool(current_item.children),
                "is_device": hasattr(current_item, 'is_device') and current_item.is_device,
                "is_loadable": hasattr(current_item, 'is_loadable') and current_item.is_loadable,
                "items": items
            }
            
            self.log_message("Retrieved {0} items at path: {1}".format(len(items), path))
            return result
            
        except Exception as e:
            self.log_message("Error getting browser items at path: {0}".format(str(e)))
            self.log_message(traceback.format_exc())
            raise
    # ---- unified additions ----

    @command("get_browser_item")
    def cmd_get_browser_item(self, params):
        uri = params.get("uri", None)
        path = params.get("path", None)
        return self._get_browser_item(uri, path)

    @command("get_browser_tree")
    def cmd_get_browser_tree(self, params):
        category_type = params.get("category_type", "all")
        return self.get_browser_tree(category_type)

    @command("get_browser_items_at_path")
    def cmd_get_browser_items_at_path(self, params):
        path = params.get("path", "")
        return self.get_browser_items_at_path(path)
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("load_instrument_or_effect", modifying=True)
    def cmd_load_instrument_or_effect(self, params):
        track_index = params.get("track_index", 0)
        uri = params.get("uri", "")
        return self._load_instrument_or_effect(track_index, uri)

    @command("load_browser_item", modifying=True)
    def cmd_load_browser_item(self, params):
        track_index = params.get("track_index", 0)
        item_uri = params.get("item_uri", "")
        return self._load_browser_item(track_index, item_uri)

    @command("browse_path")
    def cmd_browse_path(self, params):
        path = params.get("path", [])
        return self._browse_path(path)

    @command("get_browser_children")
    def cmd_get_browser_children(self, params):
        uri = params.get("uri", "")
        return self._get_browser_children(uri)

    @command("search_browser")
    def cmd_search_browser(self, params):
        query = params.get("query", "")
        category = params.get("category", "all")
        return self._search_browser(query, category)

    @command("load_browser_item_to_return", modifying=True)
    def cmd_load_browser_item_to_return(self, params):
        return_index = params.get("return_index", 0)
        item_uri = params.get("item_uri", "")
        return self._load_browser_item_to_return(return_index, item_uri)

