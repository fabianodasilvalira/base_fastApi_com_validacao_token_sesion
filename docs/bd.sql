-- --------------------------------------------------------
-- Servidor:                     localhost
-- Versão do servidor:           PostgreSQL 11.21, compiled by Visual C++ build 1914, 64-bit
-- OS do Servidor:               
-- HeidiSQL Versão:              12.10.0.7000
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES  */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

-- Copiando dados para a tabela public.alembic_version: 0 rows
/*!40000 ALTER TABLE "alembic_version" DISABLE KEYS */;
INSERT INTO "alembic_version" ("version_num") VALUES
	('84875b2b2f1f');
/*!40000 ALTER TABLE "alembic_version" ENABLE KEYS */;

-- Copiando dados para a tabela public.categorias: 0 rows
/*!40000 ALTER TABLE "categorias" DISABLE KEYS */;
INSERT INTO "categorias" ("id", "nome", "descricao", "imagem_url", "criado_em", "atualizado_em") VALUES
	(7, 'Cervejas', 'Diversas opções de cervejas nacionais e importadas, incluindo pilsen, IPA, stout, weiss e outras variedades.', 'https://exemplo.com/imagens/categorias/cervejas.jpg', '2025-05-16 10:37:33.254849-03', NULL),
	(8, 'Tira gosto', 'Petiscos e aperitivos perfeitos para acompanhar sua bebida, incluindo porções de batata frita, pastéis, iscas e outros.', 'https://exemplo.com/imagens/categorias/tiragosto.jpg', '2025-05-16 10:37:33.261776-03', NULL),
	(9, 'Destilados', 'Bebidas destiladas premium como whisky, vodka, gin, cachaça, tequila e outras opções para drinks especiais.', 'https://exemplo.com/imagens/categorias/destilados.jpg', '2025-05-16 10:37:33.263835-03', NULL),
	(1, 'Eletrônicos', 'Produtos eletrônicos em geral', 'https://exemplo.com/imagem.jpg', '2025-05-20 10:20:54.334325-03', NULL);
/*!40000 ALTER TABLE "categorias" ENABLE KEYS */;

-- Copiando dados para a tabela public.clientes: 0 rows
/*!40000 ALTER TABLE "clientes" DISABLE KEYS */;
INSERT INTO "clientes" ("id", "nome", "telefone", "observacoes", "endereco", "created_at", "updated_at", "imagem_url") VALUES
	(1, 'teste', '88888', 'tes', NULL, NULL, NULL, NULL),
	(2, 'string', 'string', 'string', 'string', '2025-05-20 10:22:11.92408', '2025-05-20 10:22:11.92408', 'string');
/*!40000 ALTER TABLE "clientes" ENABLE KEYS */;

-- Copiando dados para a tabela public.comandas: 3 rows
/*!40000 ALTER TABLE "comandas" DISABLE KEYS */;
INSERT INTO "comandas" ("id", "id_mesa", "id_cliente_associado", "status_comanda", "valor_total_calculado", "valor_pago", "valor_fiado", "valor_desconto", "motivo_cancelamento", "observacoes", "qr_code_comanda_hash", "created_at", "updated_at") VALUES
	(2, 1, 1, 'ABERTA', 0.00, 0.00, 0.00, 0.00, NULL, 'string', 'a8fcfe2b-0b07-4920-a2d5-e2600347d202', '2025-05-20 11:26:17.71637', '2025-05-20 11:26:17.71637'),
	(3, 1, 1, 'ABERTA', 0.00, 0.00, 0.00, 0.00, NULL, 'string', 'dae2bda5-7365-41be-9a59-751e7394a79e', '2025-05-20 11:26:49.072955', '2025-05-20 11:26:49.072955'),
	(1, 1, 1, 'PAGA_PARCIALMENTE', 25.00, 15.00, 0.00, 0.00, NULL, 'string', '79eb94cb-72aa-4b01-a3fd-d772380ed53a', '2025-05-20 10:49:18.802916', '2025-05-20 12:09:47.43596');
/*!40000 ALTER TABLE "comandas" ENABLE KEYS */;

-- Copiando dados para a tabela public.fiados: 0 rows
/*!40000 ALTER TABLE "fiados" DISABLE KEYS */;
/*!40000 ALTER TABLE "fiados" ENABLE KEYS */;

-- Copiando dados para a tabela public.itens_pedido: 0 rows
/*!40000 ALTER TABLE "itens_pedido" DISABLE KEYS */;
/*!40000 ALTER TABLE "itens_pedido" ENABLE KEYS */;

-- Copiando dados para a tabela public.mesas: 0 rows
/*!40000 ALTER TABLE "mesas" DISABLE KEYS */;
INSERT INTO "mesas" ("id", "numero_identificador", "capacidade", "status", "qr_code_hash", "id_cliente_associado", "ativa_para_pedidos", "criado_em", "atualizado_em") VALUES
	(1, '1', 6, 'DISPONIVEL', 'gerarhash', 1, 'true', '2025-05-20 10:41:51.651206-03', '2025-05-20 10:43:33.299174-03');
/*!40000 ALTER TABLE "mesas" ENABLE KEYS */;

-- Copiando dados para a tabela public.pagamentos: 2 rows
/*!40000 ALTER TABLE "pagamentos" DISABLE KEYS */;
INSERT INTO "pagamentos" ("id", "id_comanda", "id_cliente", "id_usuario_registrou", "id_venda", "id_pedido", "valor_pago", "metodo_pagamento", "status_pagamento", "detalhes_transacao", "observacoes", "data_pagamento", "updated_at") VALUES
	(6, 1, 1, 1, NULL, NULL, 10.00, 'DINHEIRO', 'APROVADO', NULL, 'string', '2025-05-20 12:09:21.578876', '2025-05-20 12:09:21.578876'),
	(7, 1, 1, 1, NULL, NULL, 5.00, 'PIX', 'APROVADO', NULL, 'string', '2025-05-20 12:09:47.43596', '2025-05-20 12:09:47.43596');
/*!40000 ALTER TABLE "pagamentos" ENABLE KEYS */;

-- Copiando dados para a tabela public.pedidos: 0 rows
/*!40000 ALTER TABLE "pedidos" DISABLE KEYS */;
/*!40000 ALTER TABLE "pedidos" ENABLE KEYS */;

-- Copiando dados para a tabela public.produtos: 0 rows
/*!40000 ALTER TABLE "produtos" DISABLE KEYS */;
INSERT INTO "produtos" ("id", "nome", "descricao", "preco_unitario", "disponivel", "imagem_url", "criado_em", "atualizado_em", "categoria_id") VALUES
	(2, 'IPA Artesanal', 'Cerveja amarga com alto teor de lúpulo e notas cítricas', 18.50, 'true', 'https://exemplo.com/imagens/ipa_artesanal.jpg', '2025-05-16 10:16:27.076381-03', '2025-05-16 10:37:23.471449-03', 7),
	(4, 'Stout Chocolate', 'Cerveja escura encorpada com notas de chocolate e café', 22.50, 'true', 'https://exemplo.com/imagens/stout_chocolate.jpg', '2025-05-16 10:16:27.076381-03', '2025-05-16 10:37:23.471449-03', 7),
	(3, 'Weiss Tradicional', 'Cerveja de trigo alemã com sabor frutado e refrescante', 15.90, 'true', 'https://exemplo.com/imagens/weiss_tradicional.jpg', '2025-05-16 10:16:27.076381-03', '2025-05-16 10:37:23.471449-03', 7),
	(5, 'Lager Especial', 'Cerveja leve e cristalina com sabor equilibrado', 14.90, 'true', 'https://exemplo.com/imagens/lager_especial.jpg', '2025-05-16 10:16:27.076381-03', '2025-05-16 10:37:23.471449-03', 1),
	(6, 'Whisky 12 Anos', 'Whisky escocês envelhecido por 12 anos em barris de carvalho', 189.90, 'true', 'https://exemplo.com/imagens/whisky_12anos.jpg', '2025-05-16 10:16:43.701952-03', '2025-05-16 10:37:10.889878-03', 8),
	(8, 'Gin Botânico', 'Gin artesanal com 12 botânicos selecionados', 120.00, 'true', 'https://exemplo.com/imagens/gin_botanico.jpg', '2025-05-16 10:16:43.701952-03', '2025-05-16 10:37:10.889878-03', 9),
	(9, 'Cachaça Envelhecida', 'Cachaça premium envelhecida em barril de amburana', 78.90, 'true', 'https://exemplo.com/imagens/cachaca_envelhecida.jpg', '2025-05-16 10:16:43.701952-03', '2025-05-16 10:37:10.889878-03', 1),
	(10, 'Tequila Reposado', 'Tequila mexicana envelhecida por 6 meses em barris de carvalho', 145.00, 'true', 'https://exemplo.com/imagens/tequila_reposado.jpg', '2025-05-16 10:16:43.701952-03', '2025-05-16 10:37:10.889878-03', 8),
	(7, 'Vodka Premium', 'Vodka destilada cinco vezes para máxima pureza', 95.50, 'true', 'https://exemplo.com/imagens/vodka_premium.jpg', '2025-05-16 10:16:43.701952-03', '2025-05-16 10:37:10.889878-03', 9),
	(12, 'Batata Frita com Cheddar e Bacon', 'Porção de batatas fritas crocantes cobertas com cheddar cremoso e bacon crocante', 38.50, 'true', 'https://exemplo.com/imagens/batata_cheddar_bacon.jpg', '2025-05-16 10:16:52.303902-03', '2025-05-16 10:37:26.120572-03', 9),
	(11, 'Tábua de Frios', 'Seleção de queijos e embutidos acompanhados de pães e antepastos', 65.90, 'true', 'https://exemplo.com/imagens/tabua_frios.jpg', '2025-05-16 10:16:52.303902-03', '2025-05-16 10:37:26.120572-03', 7),
	(13, 'Isca de Peixe', 'Iscas de tilápia empanadas e fritas, acompanha molho tártaro', 42.00, 'true', 'https://exemplo.com/imagens/isca_peixe.jpg', '2025-05-16 10:16:52.303902-03', '2025-05-16 10:37:26.120572-03', 7),
	(14, 'Calabresa Acebolada', 'Linguiça calabresa fatiada e grelhada com cebolas caramelizadas', 35.90, 'true', 'https://exemplo.com/imagens/calabresa_acebolada.jpg', '2025-05-16 10:16:52.303902-03', '2025-05-16 10:37:26.120572-03', 7),
	(15, 'Bolinho de Bacalhau', 'Porção com 12 bolinhos de bacalhau crocantes por fora e macios por dentro', 48.00, 'true', 'https://exemplo.com/imagens/bolinho_bacalhau.jpg', '2025-05-16 10:16:52.303902-03', '2025-05-16 10:37:26.120572-03', 7);
/*!40000 ALTER TABLE "produtos" ENABLE KEYS */;

-- Copiando dados para a tabela public.refresh_tokens: 0 rows
/*!40000 ALTER TABLE "refresh_tokens" DISABLE KEYS */;
INSERT INTO "refresh_tokens" ("id", "user_id", "token", "expires_at", "created_at") VALUES
	(1, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInVzZXJfaWQiOiIxIiwiZXhwIjoxNzQ4Mjc0MjY3LCJ0eXBlIjoicmVmcmVzaCJ9.sZOHF25Vae3a7wtymPOUc2MgegovS4wKzpIHa0GDyfY', '2025-05-26 15:44:27.499871', '2025-05-19 12:44:27.23653'),
	(2, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInVzZXJfaWQiOiIxIiwiZXhwIjoxNzQ4Mjc1Nzg1LCJ0eXBlIjoicmVmcmVzaCJ9.OIHQaO5ef_uPGhfzlRydt2OrSNCpvodVO-sUwZWPoIU', '2025-05-26 16:09:45.217346', '2025-05-19 13:09:44.995553');
/*!40000 ALTER TABLE "refresh_tokens" ENABLE KEYS */;

-- Copiando dados para a tabela public.users: 0 rows
/*!40000 ALTER TABLE "users" DISABLE KEYS */;
INSERT INTO "users" ("id", "email", "username", "hashed_password", "first_name", "last_name", "phone", "imagem_url", "is_verified", "is_active", "is_superuser", "created_at", "updated_at") VALUES
	(1, 'admin@example.com', 'admin', '$2b$12$L1SJvGnGBa5dF55jKqkS0.knZf3sjghW9f4HIfCC39ZhDW.80.brK', 'Administrador', NULL, NULL, NULL, 'false', 'true', 'true', '2025-05-19 12:44:03.844529', '2025-05-19 12:44:03.844529');
/*!40000 ALTER TABLE "users" ENABLE KEYS */;

-- Copiando dados para a tabela public.vendas: 0 rows
/*!40000 ALTER TABLE "vendas" DISABLE KEYS */;
/*!40000 ALTER TABLE "vendas" ENABLE KEYS */;

-- Copiando dados para a tabela public.venda_produto: 0 rows
/*!40000 ALTER TABLE "venda_produto" DISABLE KEYS */;
/*!40000 ALTER TABLE "venda_produto" ENABLE KEYS */;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
