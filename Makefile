PREFIX ?= $(HOME)/.local
INSTALL_PATH = $(DESTDIR)$(PREFIX)/share/albert/org.albert.extension.python/modules

all:
	@echo "Run 'make install' to install this Albert extension

clean:
	@rm -rf "$(INSTALL_PATH)/lyx_shortcuts"

install:
	@mkdir -p "$(INSTALL_PATH)/lyx_shortcuts"
	@cp -v src/* "$(INSTALL_PATH)/lyx_shortcuts"
