# Weather Pipeline 🌦️

Pipeline pessoal de dados (ETL) que coleta dados de clima em tempo real via API,
trata e estrutura os dados, carrega num banco relacional e alimenta um dashboard
de visualização — rodando de forma automatizada e agendada.

Projeto criado para praticar, na prática, os mesmos conceitos que aplico
profissionalmente em migração e engenharia de dados: extração de fontes
externas, validação e transformação de dados, carga em banco relacional e
automação de execução.

## 📊 Resultado

![Variação de temperatura por cidade](images/grafico_temperatura.png)

Gráfico gerado no Power BI a partir dos dados tratados, mostrando a variação
de temperatura em três cidades brasileiras ao longo de agosto de 2026.

## 🏗️ Arquitetura do pipeline

```
OpenWeather API
      │
      ▼
[1] extract_weather.py   → coleta dados brutos e salva em raw/*.json
      │
      ▼
[2] transform_weather.py → limpa, estrutura e calcula métricas → processed/*.csv
      │
      ▼
[3] load_to_mysql.py     → carrega os dados tratados no MySQL (idempotente)
      │
      ▼
   Power BI               → dashboard de visualização
```

A execução das três etapas é automatizada diariamente via **Agendador de
Tarefas do Windows**, através do script `run_pipeline.bat`.

## 🛠️ Tecnologias

- **Python** — extração, transformação e carga dos dados
- **Pandas** — limpeza, estruturação e cálculo de métricas
- **MySQL** — armazenamento relacional dos dados tratados
- **Power BI** — visualização e dashboard
- **OpenWeather API** — fonte dos dados de clima

## ✨ Principais decisões técnicas

- **Idempotência na carga**: a tabela usa uma constraint `UNIQUE(cidade, timestamp_coleta_unix)`
  combinada com `INSERT IGNORE`, permitindo rodar o pipeline quantas vezes
  forem necessárias sem gerar dados duplicados.
- **Dado bruto preservado**: a etapa de extração sempre salva o JSON original
  antes de qualquer transformação, permitindo reprocessar o histórico se as
  regras de transformação mudarem no futuro.
- **Tratamento de erros de rede**: timeouts, erros HTTP e falhas de conexão
  são tratados individualmente, sem derrubar a execução das outras cidades.
- **Credenciais fora do código**: chave de API e credenciais do banco ficam
  em variáveis de ambiente (`.env`, não versionado).

## 🚀 Como rodar

1. Clone o repositório e crie um ambiente virtual:
   ```bash
   git clone <url-do-repo>
   cd weather-pipeline
   python -m venv venv
   source venv/Scripts/activate   # Windows
   ```

2. Instale as dependências:
   ```bash
   pip install -r requirements.txt
   ```

3. Copie `.env.example` para `.env` e preencha com sua chave da
   [OpenWeather API](https://openweathermap.org/api) e as credenciais do seu
   MySQL local.

4. Rode o pipeline completo:
   ```bash
   python extract_weather.py
   python transform_weather.py
   python load_to_mysql.py
   ```

## 📈 Possíveis evoluções

- Migrar a carga de MySQL local para um data warehouse em nuvem (BigQuery/Redshift)
- Orquestrar as etapas com Apache Airflow em vez do Agendador de Tarefas
- Adicionar testes automatizados para as regras de transformação

---

Desenvolvido por [Nathan Anaquim Procaccia](https://www.linkedin.com/in/nathan-anaquim-procaccia-8a8420277/)
