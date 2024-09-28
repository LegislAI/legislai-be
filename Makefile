PYTHON_VERSION = $(cat .python-version)
VENV_NAME = $(shell cat .python-env 2>/dev/null)
PYENV = pyenv
PIP = pip3
REQUIREMENTS = requirements.txt
CURRENT_SHELL = $(notdir $(SHELL))

all: check-files install-python create-venv install-requirements

check-files:
	@if [ ! -f .python-version ]; then \
		echo ".python-version não existe!"; \
		exit 1; \
	fi
	@if [ ! -f .python-env ]; then \
		echo ".python-env não existe!"; \
		exit 1; \
	fi

install-pyenv:
ifeq ($(CURRENT_SHELL), bash)
	@if ! command -v pyenv >/dev/null; then \
		curl https://pyenv.run | bash; \
	fi
	@echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
	@echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
	@echo 'eval "$(pyenv init -)"' >> ~/.bashrc
else ifeq ($(CURRENT_SHELL), zsh)
	@if ! command -v pyenv >/dev/null; then \
		curl https://pyenv.run | zsh; \
	fi
	@echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
	@echo '[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc
	@echo 'eval "$(pyenv init -)"' >> ~/.zshrc
endif

install-python: install-pyenv
	@if ! $(PYENV) versions --bare | grep -q "^$(PYTHON_VERSION)$$"; then \
		$(PYENV) install --skip-existing $(PYTHON_VERSION); \
	fi
	$(PYENV) global $(PYTHON_VERSION)

create-venv:
	@if ! $(PYENV) virtualenvs --bare | grep -q $(VENV_NAME); then \
		$(PYENV) virtualenv $(PYTHON_VERSION) $(VENV_NAME); \
	fi
	$(PYENV) local $(VENV_NAME)

install-requirements:
	$(PIP) install -r $(REQUIREMENTS) --break-system-packages





# TODO:
# usar o nome da pasta invés de legislai-backend
# primeiro if, verificar se exsitem pastas como versãoi e nome ambiente