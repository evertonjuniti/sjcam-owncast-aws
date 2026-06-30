# Configuração do EventBridge
![Owncast-Lambda.svg](/Images/Owncast-EventBridge.svg)

## Observação importante: aqui estou assumindo que nesta parte opcional você deseja tanto desligar as instâncias EC2 do Owncast e HAProxy, quanto atualizá-los através da função Lambda de manutenção

### Para desligar automaticamente as instâncias EC2 do Owncast e do HAProxy todos os dias às 00:00h:

- Crie um novo EventBridge Schedule na mesma region da suas instâncias EC2
  - Schedule name: defina um nome para o agendamento, no meu exemplo ficou OwncastStopEC2Instances
  - Description: é opcional
  - Schedule group: pode manter o "default"
  - Schedule patterns: selecione a opção "Recurring schedule"
  - Time zone: escolha o de sua preferência (é possível que já esteja selecionado o default para sua Region)
  - Schedule type: pode escolher a que achar melhor, neste exemplo foi escolhido "Cron-based schedule"
  - Cron expression (sugestão para executar todos os dias às 00:00h):
    - Minutes: 0
    - Hours: 0
    - Day of the month: *
    - Month: *
    - Day of the week: ?
    - Year: *
  - Flexible time window: selecione a opção "Off" no combo-box
  - Timeframe: pode deixar os campos sem valor nenhum (que é o default)
  - Clique no botão Next
  - Em Target API, selecione a opção "All APIs"
    - No campo de busca "Find service", digite "EC2" e depois selecione a opção "Amazon EC2 (502)"
    - No campo de busca "Find API", digite "Stop" e depois selecione a opção "StopInstances"
    - No quadro mais abaixo que surgir, inclua na lista os IDs de ambas as intâncias EC2 referentes à instância em que está instalado o Owncast e a instância em que está instalado o HAProxy
  - Clique no botão Next
  - Schedule state: mantenha habilitado (Enable)
  - Action after schedule completion: pode manter vazio (sem selecionar nenhuma opção)
  - Retry policy: pode manter desabilitado
    - Dead-letter queue (DLQ): mantenha selecionada a opção "None"
  - Customize encrption settings (advanced): não checar a opção
  - Permissions: você será obrigado a selecionar uma Role, portanto só haverá a opção "Use existing role"
  - Select an existing role: selecione a Role específica, no meu exemplo ela se chama OwncastStopEC2InstanceRole
  - Clique no botão Next
  - Revise as configurações e clique no botão "Create schedule"

### Para atualizar automaticamente as instâncias EC2 do Owncast e do HAProxy:

#### Cron Schedule para atualizar a instância EC2 do Owncast, executando no primeiro dia do mês às 01:00h:

- Crie um novo EventBridge Schedule na mesma region da suas instâncias EC2
  - Schedule name: defina um nome para o agendamento, no meu exemplo ficou Owncast_OS_Update
  - Description: é opcional
  - Schedule group: pode manter o "default"
  - Schedule patterns: selecione a opção "Recurring schedule"
  - Time zone: escolha o de sua preferência (é possível que já esteja selecionado o default para sua Region)
  - Schedule type: pode escolher a que achar melhor, neste exemplo foi escolhido "Cron-based schedule"
  - Cron expression (sugestão para executar todo primeiro dia do mês, às 01:00h):
    - Minutes: 0
    - Hours: 1
    - Day of the month: 1
    - Month: *
    - Day of the week: ?
    - Year: *
  - Flexible time window: selecione a opção "Off" no combo-box
  - Timeframe: pode deixar os campos sem valor nenhum (que é o default)
  - Clique no botão Next
  - Em Target API, selecione a opção "Templated targets"
  - Selecione a opção "AWS Lambda"
  - Lambda function: selecione a Lambda Function de manutenção, no meu caso ela se chama "OwncastMaintenance"
  - Payload: insira o seguinte valor -> {"mode":"owncast-os-update"}
  - Clique no botão Next
  - Schedule state: mantenha habilitado (Enable)
  - Action after schedule completion: pode manter vazio (sem selecionar nenhuma opção)
  - Retry policy: pode manter desabilitado
    - Dead-letter queue (DLQ): mantenha selecionada a opção "None"
  - Customize encrption settings (advanced): não checar a opção
  - Permissions: você poderá criar uma nova Role já preparada para este tipo de execução, ou poderá selecionar a opção "Use existing role" caso já tenha uma role
  - Select an existing role: selecione a Role específica, no meu exemplo ela se chama Amazon_EventBridge_Scheduler_LAMBDA (no meu caso eu criei no primeiro schedule e a reutilizei nas demais)
  - Clique no botão Next
  - Revise as configurações e clique no botão "Create schedule"

#### Cron Schedule para atualizar a instância EC2 do HAProxy, executando no primeiro dia do mês às 01:30h:

- Crie um novo EventBridge Schedule na mesma region da suas instâncias EC2
  - Schedule name: defina um nome para o agendamento, no meu exemplo ficou Proxy_OS_Update
  - Description: é opcional
  - Schedule group: pode manter o "default"
  - Schedule patterns: selecione a opção "Recurring schedule"
  - Time zone: escolha o de sua preferência (é possível que já esteja selecionado o default para sua Region)
  - Schedule type: pode escolher a que achar melhor, neste exemplo foi escolhido "Cron-based schedule"
  - Cron expression (sugestão para executar todo primeiro dia do mês, às 01:30h):
    - Minutes: 30
    - Hours: 1
    - Day of the month: 1
    - Month: *
    - Day of the week: ?
    - Year: *
  - Flexible time window: selecione a opção "Off" no combo-box
  - Timeframe: pode deixar os campos sem valor nenhum (que é o default)
  - Clique no botão Next
  - Em Target API, selecione a opção "Templated targets"
  - Selecione a opção "AWS Lambda"
  - Lambda function: selecione a Lambda Function de manutenção, no meu caso ela se chama "OwncastMaintenance"
  - Payload: insira o seguinte valor -> {"mode":"proxy-os-update"}
  - Clique no botão Next
  - Schedule state: mantenha habilitado (Enable)
  - Action after schedule completion: pode manter vazio (sem selecionar nenhuma opção)
  - Retry policy: pode manter desabilitado
    - Dead-letter queue (DLQ): mantenha selecionada a opção "None"
  - Customize encrption settings (advanced): não checar a opção
  - Permissions: você poderá criar uma nova Role já preparada para este tipo de execução, ou poderá selecionar a opção "Use existing role" caso já tenha uma role
  - Select an existing role: selecione a Role específica, no meu exemplo ela se chama Amazon_EventBridge_Scheduler_LAMBDA (no meu caso eu criei no primeiro schedule e a reutilizei nas demais)
  - Clique no botão Next
  - Revise as configurações e clique no botão "Create schedule"

#### Cron Schedule para atualizar o certificado digital para a instância EC2 do HAProxy, executando no primeiro dia do mês às 02:00h:

- Crie um novo EventBridge Schedule na mesma region da suas instâncias EC2
  - Schedule name: defina um nome para o agendamento, no meu exemplo ficou Proxy_Cert_Renew
  - Description: é opcional
  - Schedule group: pode manter o "default"
  - Schedule patterns: selecione a opção "Recurring schedule"
  - Time zone: escolha o de sua preferência (é possível que já esteja selecionado o default para sua Region)
  - Schedule type: pode escolher a que achar melhor, neste exemplo foi escolhido "Cron-based schedule"
  - Cron expression (sugestão para executar todo primeiro dia do mês, às 02:00h):
    - Minutes: 00
    - Hours: 2
    - Day of the month: 1
    - Month: *
    - Day of the week: ?
    - Year: *
  - Flexible time window: selecione a opção "Off" no combo-box
  - Timeframe: pode deixar os campos sem valor nenhum (que é o default)
  - Clique no botão Next
  - Em Target API, selecione a opção "Templated targets"
  - Selecione a opção "AWS Lambda"
  - Lambda function: selecione a Lambda Function de manutenção, no meu caso ela se chama "OwncastMaintenance"
  - Payload: insira o seguinte valor -> {"mode":"proxy-cert-renew"}
  - Clique no botão Next
  - Schedule state: mantenha habilitado (Enable)
  - Action after schedule completion: pode manter vazio (sem selecionar nenhuma opção)
  - Retry policy: pode manter desabilitado
    - Dead-letter queue (DLQ): mantenha selecionada a opção "None"
  - Customize encrption settings (advanced): não checar a opção
  - Permissions: você poderá criar uma nova Role já preparada para este tipo de execução, ou poderá selecionar a opção "Use existing role" caso já tenha uma role
  - Select an existing role: selecione a Role específica, no meu exemplo ela se chama Amazon_EventBridge_Scheduler_LAMBDA (no meu caso eu criei no primeiro schedule e a reutilizei nas demais)
  - Clique no botão Next
  - Revise as configurações e clique no botão "Create schedule"

---
[⬅️ Anterior: Configuração da Função Lambda](11-Lambda.md) | [🏠 Índice](../README.md) | [Próximo: Configuração do API Gateway ➡️](13-API-Gateway.md)