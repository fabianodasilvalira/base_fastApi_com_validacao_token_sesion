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
	('cba1cf48d1e7');
/*!40000 ALTER TABLE "alembic_version" ENABLE KEYS */;

-- Copiando dados para a tabela public.categorias: 0 rows
/*!40000 ALTER TABLE "categorias" DISABLE KEYS */;
INSERT INTO "categorias" ("id", "nome", "descricao", "imagem_url", "criado_em", "atualizado_em") VALUES
	(7, 'Cervejas', 'Diversas opções de cervejas nacionais e importadas, incluindo pilsen, IPA, stout, weiss e outras variedades.', 'https://exemplo.com/imagens/categorias/cervejas.jpg', '2025-05-16 10:37:33.254849-03', NULL),
	(8, 'Tira gosto', 'Petiscos e aperitivos perfeitos para acompanhar sua bebida, incluindo porções de batata frita, pastéis, iscas e outros.', 'https://exemplo.com/imagens/categorias/tiragosto.jpg', '2025-05-16 10:37:33.261776-03', NULL),
	(9, 'Destilados', 'Bebidas destiladas premium como whisky, vodka, gin, cachaça, tequila e outras opções para drinks especiais.', 'https://exemplo.com/imagens/categorias/destilados.jpg', '2025-05-16 10:37:33.263835-03', NULL),
	(1, 'Eletrônicos', 'Produtos eletrônicos em geral', 'https://exemplo.com/imagem.jpg', '2025-05-20 10:20:54.334325-03', NULL);
/*!40000 ALTER TABLE "categorias" ENABLE KEYS */;

-- Copiando dados para a tabela public.clientes: 2 rows
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
	(1, 1, 1, 'PAGA_PARCIALMENTE', 0.00, 0.00, 0.00, 0.00, NULL, 'string', '79eb94cb-72aa-4b01-a3fd-d772380ed53a', '2025-05-20 10:49:18.802916', '2025-05-21 12:36:18.133107');
/*!40000 ALTER TABLE "comandas" ENABLE KEYS */;

-- Copiando dados para a tabela public.fiados: 0 rows
/*!40000 ALTER TABLE "fiados" DISABLE KEYS */;
/*!40000 ALTER TABLE "fiados" ENABLE KEYS */;

-- Copiando dados para a tabela public.itens_pedido: 9 rows
/*!40000 ALTER TABLE "itens_pedido" DISABLE KEYS */;
INSERT INTO "itens_pedido" ("id", "id_pedido", "id_comanda", "id_produto", "quantidade", "preco_unitario", "observacoes", "status", "created_at", "updated_at", "preco_total") VALUES
	(2, 12, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:06:12.159294', '2025-05-21 12:06:12.159294', 37.00),
	(3, 13, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:10:29.57125', '2025-05-21 12:10:29.57125', 37.00),
	(4, 14, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:10:57.762725', '2025-05-21 12:10:57.762725', 37.00),
	(5, 15, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:12:11.734979', '2025-05-21 12:12:11.734979', 37.00),
	(6, 16, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:15:24.133981', '2025-05-21 12:15:24.133981', 37.00),
	(7, 17, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:31:38.071278', '2025-05-21 12:31:38.071278', 37.00),
	(8, 19, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:34:58.631061', '2025-05-21 12:34:58.631061', 37.00),
	(9, 20, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:35:59.226831', '2025-05-21 12:35:59.226831', 37.00),
	(10, 21, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:36:18.133107', '2025-05-21 12:36:18.133107', 37.00),
	(11, 22, 1, 2, 2, 18.50, 'string', 'RECEBIDO', '2025-05-21 12:37:38.082011', '2025-05-21 12:37:38.082011', 37.00);
/*!40000 ALTER TABLE "itens_pedido" ENABLE KEYS */;

-- Copiando dados para a tabela public.mesas: 1 rows
/*!40000 ALTER TABLE "mesas" DISABLE KEYS */;
INSERT INTO "mesas" ("id", "numero_identificador", "capacidade", "status", "qr_code_hash", "id_cliente_associado", "ativa_para_pedidos", "criado_em", "atualizado_em") VALUES
	(1, '1', 6, 'DISPONIVEL', 'gerarhash', 1, 'true', '2025-05-20 10:41:51.651206-03', '2025-05-20 10:43:33.299174-03');
/*!40000 ALTER TABLE "mesas" ENABLE KEYS */;

-- Copiando dados para a tabela public.pagamentos: 0 rows
/*!40000 ALTER TABLE "pagamentos" DISABLE KEYS */;
INSERT INTO "pagamentos" ("id", "id_comanda", "id_cliente", "id_usuario_registrou", "id_venda", "id_pedido", "valor_pago", "metodo_pagamento", "status_pagamento", "detalhes_transacao", "observacoes", "data_pagamento", "updated_at") VALUES
	(6, 1, 1, 1, NULL, NULL, 10.00, 'DINHEIRO', 'APROVADO', NULL, 'string', '2025-05-20 12:09:21.578876', '2025-05-20 12:09:21.578876'),
	(7, 1, 1, 1, NULL, NULL, 5.00, 'PIX', 'APROVADO', NULL, 'string', '2025-05-20 12:09:47.43596', '2025-05-20 12:09:47.43596');
/*!40000 ALTER TABLE "pagamentos" ENABLE KEYS */;

-- Copiando dados para a tabela public.pedidos: 10 rows
/*!40000 ALTER TABLE "pedidos" DISABLE KEYS */;
INSERT INTO "pedidos" ("id", "id_comanda", "id_usuario_registrou", "mesa_id", "tipo_pedido", "status_geral_pedido", "observacoes_pedido", "motivo_cancelamento", "created_at", "updated_at") VALUES
	(12, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:06:12.140887', '2025-05-21 12:06:12.140887'),
	(13, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:10:29.542968', '2025-05-21 12:10:29.542968'),
	(14, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:10:57.732525', '2025-05-21 12:10:57.732525'),
	(15, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:12:11.721336', '2025-05-21 12:12:11.721336'),
	(16, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:15:24.119782', '2025-05-21 12:15:24.119782'),
	(17, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:31:38.040129', '2025-05-21 12:31:38.040129'),
	(19, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:34:58.629525', '2025-05-21 12:34:58.629525'),
	(20, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:35:59.225831', '2025-05-21 12:35:59.225831'),
	(21, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:36:18.128135', '2025-05-21 12:36:18.128135'),
	(22, 1, 1, 1, 'INTERNO_MESA', 'RECEBIDO', 'string', NULL, '2025-05-21 12:37:38.064664', '2025-05-21 12:37:38.064664');
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
