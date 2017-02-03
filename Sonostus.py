#!/usr/bin/env python

import json
import os
import threading

from envparse import env

import soco
import rumps
from rumps import MenuItem
from soco import SoCo

rumps.debug_mode(env.bool("DEBUG", default=False))

try:
    from urllib import urlretrieve
except ImportError:
    from urllib.request import urlretrieve

class SonostusApp(rumps.App):
    def update_zones(self):
        self.zones = list(soco.discover())
        try:
            with self.open('zones.json', 'w') as f:
                json.dump([{'ip_address': z.ip_address, 'player_name': z.player_name} for z in self.zones], f)
        except:
            pass

        self.update_zone_menu()
        return self.zones

    def update_zones_fork(self, sender):
        t = threading.Thread(target=self.update_zones)
        t.start()

    def select_zone(self, sender):
        self.zone = [z for z in self.zones if z.player_name == sender.title][0]
        for mi in self.menu['Zones'].itervalues():
            mi.state = 0
        sender.state = 1
        self.menu['Mute'].state = 1 if self.zone.mute else 0

    def update_zone_menu(self):
        players = []
        for z in self.zones:
            menuitem = MenuItem(z.player_name, callback=self.select_zone)
            menuitem.state = 1 if self.zone == z else 0
            players.append(menuitem)
        players.append(MenuItem('Update zones', callback=self.update_zones_fork))
        if self.menu['Zones']:
            self.menu['Zones'].clear()
        self.menu['Zones'].update(players)

    @rumps.timer(2)
    def update_title(self,_):
        track = self.zone.group.coordinator.get_current_track_info()
        title = "%s: %s" % (track['artist'], track['title'])
        album = track['album']
        uri = track['album_art']
        if not (self.title and self.title == title):
            self.title = None
            self.title = title
        if uri and not self.uri == title:
            self.uri = uri
            filename = os.path.join(rumps.application_support(self.name), 'track.jpeg')
            urlretrieve (uri, filename)
            if self.menu['Album info']:
                self.menu['Album info'].clear()
            art = MenuItem(album, icon=filename, dimensions=[256, 256], callback=lambda x: None)
            self.menu['Album info'].update(art)
        self.menu['Mute'].state = 1 if self.zone.mute else 0


    @rumps.clicked('Mute')
    def mute(self, sender):
        self.zone.mute = not self.zone.mute
        sender.state = 1 if self.zone.mute else 0

    @rumps.clicked('Next')
    def pause(self, sender):
        self.zone.group.coordinator.next()

    @rumps.clicked('Previous')
    def pause(self, sender):
        self.zone.group.coordinator.previous()

    @rumps.clicked('Pause/Play')
    def pause(self, sender):
        z = self.zone.group.coordinator
        if z.get_current_transport_info()['current_transport_state'] == 'PLAYING':
            z.pause()
        else:
            z.play()

    @rumps.clicked('Volume up')
    def volume_up(self, _e):
        self.zone.volume = self.zone.volume + 2

    @rumps.clicked('Volume down')
    def volume_up(self, _e):
        self.zone.volume = self.zone.volume - 2

if __name__ == "__main__":
    app = SonostusApp("Sonostus", title="Sonostus", quit_button=rumps.MenuItem('Quit', key='q'))
    try:
        with app.open('zones.json', 'r') as f:
            j = json.load(f)
            app.zones = [SoCo(z['ip_address']) for z in j]
    except Exception as e:
        app.zones = [SoCo('10.0.1.2'), SoCo('10.0.1.11')]
        app.update_zones_fork(None)

    app.zone = app.zones[0]
    app.icon = 'images/sonos_icon.png'
    app.uri = None

    app.menu = [('Album info', []),
                ('Zones',[]),
                rumps.separator,
                'Mute',
                'Next',
                'Previous',
                'Pause/Play',
                'Volume up',
                'Volume down',
                rumps.separator
                ]
    app.update_zone_menu()
    app.run()
