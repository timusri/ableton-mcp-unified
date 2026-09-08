"""Chain command handlers.

The ``cmd_*`` adapters are registered through registry.py.
"""
import random
import traceback

from ..registry import command


class ChainHandlers(object):

    def _get_rack_chains(self, track_index, device_index):
        """Get chains from an instrument/effect rack"""
        try:
            track = self._validate_track_index(track_index)
            device = self._validate_device_index(track, device_index)

            if not device.can_have_chains:
                return {"error": "Device is not a rack", "device_name": device.name}

            chains = []
            for i, chain in enumerate(device.chains):
                chains.append({
                    "index": i,
                    "name": chain.name,
                    "mute": chain.mute,
                    "solo": chain.solo,
                    "device_count": len(chain.devices)
                })

            return {
                "track_index": track_index,
                "device_index": device_index,
                "device_name": device.name,
                "chain_count": len(chains),
                "chains": chains
            }
        except Exception as e:
            self.log_message("Error getting rack chains: " + str(e))
            raise
    def _select_rack_chain(self, track_index, device_index, chain_index):
        """Select a chain in a rack"""
        try:
            track = self._validate_track_index(track_index)
            device = self._validate_device_index(track, device_index)

            if not device.can_have_chains:
                raise ValueError("Device is not a rack")

            if chain_index < 0 or chain_index >= len(device.chains):
                raise IndexError("Chain index out of range")

            # Select the chain
            if hasattr(device, 'view') and hasattr(device.view, 'selected_chain_index'):
                device.view.selected_chain_index = chain_index

            return {
                "track_index": track_index,
                "device_index": device_index,
                "chain_index": chain_index,
                "chain_name": device.chains[chain_index].name
            }
        except Exception as e:
            self.log_message("Error selecting rack chain: " + str(e))
            raise
    def _get_chain_info(self, track_index, device_index, chain_index=None):
        """Get chain information for a rack device."""
        try:
            track, device = self._resolve_device(track_index, device_index)

            if not device.can_have_chains:
                raise ValueError("Device '{0}' is not a rack and has no chains".format(device.name))

            if chain_index is not None:
                # Detail for a specific chain
                chains = device.chains
                if chain_index < 0 or chain_index >= len(chains):
                    raise IndexError("Chain index {0} out of range".format(chain_index))
                chain = chains[chain_index]
                devices = []
                for di, d in enumerate(chain.devices):
                    devices.append({
                        "index": di,
                        "name": d.name,
                        "class_name": d.class_name,
                        "type": self._get_device_type(d),
                        "is_active": d.is_active,
                        "parameter_count": len(d.parameters),
                    })
                return {
                    "chain_name": chain.name,
                    "devices": devices,
                }
            else:
                # List all chains
                chain_list = []
                for ci, chain in enumerate(device.chains):
                    chain_devices = []
                    for di, d in enumerate(chain.devices):
                        chain_devices.append({
                            "index": di,
                            "name": d.name,
                            "type": self._get_device_type(d),
                        })
                    chain_list.append({
                        "index": ci,
                        "name": chain.name,
                        "mute": chain.mute,
                        "solo": chain.solo,
                        "device_count": len(chain.devices),
                        "devices": chain_devices,
                    })
                return {
                    "device_name": device.name,
                    "chain_count": len(device.chains),
                    "chains": chain_list,
                }
        except Exception as e:
            self.log_message("Error getting chain info: " + str(e))
            raise
    # ---- unified additions ----

    @command("get_chain_info")
    def cmd_get_chain_info(self, params):
        ti = params.get("track_index", 0)
        di = params.get("device_index", 0)
        ci = params.get("chain_index", None)
        return self._get_chain_info(ti, di, ci)
    # ---- command adapters (generated from the original dispatch chain) ----

    @command("get_rack_chains", modifying=True)
    def cmd_get_rack_chains(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        return self._get_rack_chains(track_index, device_index)

    @command("select_rack_chain", modifying=True)
    def cmd_select_rack_chain(self, params):
        track_index = params.get("track_index", 0)
        device_index = params.get("device_index", 0)
        chain_index = params.get("chain_index", 0)
        return self._select_rack_chain(track_index, device_index, chain_index)

