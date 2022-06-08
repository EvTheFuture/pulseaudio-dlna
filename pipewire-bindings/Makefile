# This file is part of pulseaudio-dlna.

# pulseaudio-dlna is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# pulseaudio-dlna is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pulseaudio-dlna.  If not, see <http://www.gnu.org/licenses/>.

ifdef DEB_HOST_ARCH
PREFIX ?= usr/
else
PREFIX ?= /usr/local
endif

DESTDIR ?= /

all: clean lib

install:
	install -m644 -D libpipewire-bindings.so "${DESTDIR}${PREFIX}/lib/libpipewire-bindings.so"

lib:
	gcc -I /usr/include/spa-0.2 -I /usr/include/pipewire-0.3 -shared -o libpipewire-bindings.so -fPIC pipewire-bindings.c -L /usr/lib -l pipewire-0.3

clean:
	rm -f *.so
