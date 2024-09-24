PYTHON_VERSION = $(cat .python-version)
VENV_NAME = $(cat .python-env)
PYENV = pyenv
PIP = pip3
REQUIREMENTS = requirements.txt
CURRENT_SHELL = $(notdir $(SHELL))

all: install-python create-venv install-requirements

install-pyenv:
	@if ! command -v pyenv >/dev/null; then \
		git clone https://github.com/pyenv/pyenv.git ~/.pyenv; \
	fi
ifeq ($(CURRENT_SHELL), bash)
	@echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
	@echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
	@echo 'eval "$(pyenv init -)"' >> ~/.bashrc
else ifeq ($(CURRENT_SHELL), zsh)
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
	@if ! $(PYENV) virtualenvs --bare | grep -q legislai-backend; then \
		$(PYENV) virtualenv $(PYTHON_VERSION) legislai-backend; \
	fi
	$(PYENV) local legislai-backend

install-requirements:
	$(PIP) install -r $(REQUIREMENTS) --break-system-packages
