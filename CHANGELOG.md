# Project Changelog

## [2026-01-29 17:10]

### Added
- Novo sistema de configuracao baseado em TOML com dataclasses tipadas (`settings/`)
  - `schema.py`: Dataclasses para todas as secoes (BrandingConfig, ColorsConfig, FontsConfig, LayoutConfig, etc.)
  - `defaults.py`: Valores default para Agora Investimentos
  - `loader.py`: Carregamento TOML com merge de multiplas fontes
- Suporte a arquivos de configuracao:
  - `.charting.toml` ou `charting.toml` na raiz do projeto
  - Secao `[tool.charting]` no `pyproject.toml`
  - Config global do usuario (`~/.config/charting/config.toml`)
- Arquivo `charting.example.toml` com todas as opcoes documentadas
- Nova documentacao `docs/configuration.md` com guia completo de configuracao
- Funcao `reset_config()` para resetar configuracoes para defaults
- Funcao `get_charts_path()` e `get_outputs_path()` como alternativa as constantes

### Changed
- Refatorado sistema de configuracao: de `config.py` (auto-discovery simples) para `settings/` (TOML + dataclasses)
- `AgoraTheme` renomeado para `ChartingTheme` com lazy loading de configuracoes
- Todos os modulos agora usam `get_config()` para acessar configuracoes em vez de valores hardcoded:
  - `components/footer.py`: branding e layout do footer configuraveis
  - `components/markers.py`: tamanhos de scatter e offsets de labels configuraveis
  - `components/collision.py`: margens e thresholds de colisao configuraveis
  - `overlays/bands.py`: alpha default configuravel
  - `overlays/moving_average.py`: estilo de linha configuravel
  - `overlays/reference_lines.py`: estilos de linhas ATH/ATL configuraveis
  - `plots/line.py` e `plots/bar.py`: espessuras e estilos configuraveis
  - `styling/fonts.py`: tamanhos de fonte configuraveis
  - `styling/formatters.py`: formatos e separadores configuraveis
  - `engine.py`: figsize e dpi configuraveis
- Parametros com defaults hardcoded agora usam `None` e resolvem via config
- Documentacao `docs/architecture.md` atualizada com nova estrutura
- Documentacao `docs/getting-started.md` atualizada com exemplos de configuracao

### Removed
- Arquivo `config.py` removido (substituido por `settings/`)
- Constantes hardcoded removidas de todos os modulos (movidas para config)
