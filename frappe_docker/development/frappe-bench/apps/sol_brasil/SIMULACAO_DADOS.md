# Massa de dados de simulação

O script `sol_brasil.simulation.populate_realistic_demo` cria uma massa idempotente com, no mínimo:

- 200 clientes com códigos numéricos, CPF, telefone e endereço;
- contratos e credenciais PPPoE cujos estados são calculados pelas regras de atraso; cancelamentos da amostra são feitos explicitamente pelo script;
- uma OLT com 4 slots e 16 PONs por slot;
- 64 CTOs de 8 portas, totalizando 512 portas;
- uma fatura por cliente, incluindo títulos em aberto, vencidos e pagos;
- atendimentos fictícios para uma amostra dos clientes.

Todos os registros financeiros possuem indicação explícita de que são fictícios.

## Executar em outra instalação

Depois de atualizar o aplicativo `sol_brasil` e executar as migrações, rode a partir da pasta do bench:

```bash
bench --site SEU_SITE execute sol_brasil.simulation.populate_realistic_demo
```

O comando pode ser executado novamente. Os registros existentes são reutilizados e não são duplicados.
