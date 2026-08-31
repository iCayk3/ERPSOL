# Runbook de sombra, piloto e expansão

## Pré-condições

- Backup do ERP e do banco RADIUS restaurado em ambiente descartável.
- Relatório sem usuário duplicado e sem contrato ativo sem senha/plano.
- Relógios ERP, RADIUS e NAS sincronizados por NTP.
- Access-Accept, Reject, Rate-Limit, IP/pool, limite de sessão e accounting aprovados no laboratório.
- Usuário administrativo local de emergência no NAS.

## Modo sombra

1. Mantenha a autenticação atual como autoridade.
2. Provisione todos os contratos no novo banco e compare totais por estado e plano.
3. Envie accounting somente do NAS de laboratório ou de um grupo autorizado.
4. Monitore fila pendente/erro, sessões sem Stop, divergências e latência por um ciclo de cobrança.
5. Não envie Disconnect a clientes fora do grupo autorizado.

Critério: zero credenciais ausentes/duplicadas, fila estável e divergências explicadas.

## Piloto

1. Selecione um NAS/área isolável, excluindo clientes críticos.
2. Registre janela, responsáveis, lista de contratos e configuração anterior do NAS.
3. Reprocesse a reconciliação e confirme fila zerada.
4. Configure primário e secundário no NAS e migre somente o grupo aprovado.
5. Valide autenticação, velocidade, endereço, sessões, consumo, redução, bloqueio, pagamento e desbloqueio.
6. Observe por pelo menos 24 horas e registre incidentes.

Rollback: restaure os servidores RADIUS anteriores no NAS. Não apague accounting nem eventos coletados.

## Expansão e alta disponibilidade

- Execute por lotes identificáveis de NAS/região.
- Hospede os dois RADIUS em zonas diferentes e teste a perda individual de cada um.
- Use banco altamente disponível ou recuperação com RPO/RTO formalmente aprovados.
- Restrinja UDP 1812/1813/3799 por firewall; use VPN ou RadSec em redes não confiáveis.
- Alerte para serviço indisponível, rejeições anormais, fila com erro, falta de accounting e sessões presas.
- Teste trimestralmente restauração, perda de Stop, falha do banco e retorno do primário.

Cada lote exige evidência assinada de testes e decisão explícita de continuar ou retornar.
