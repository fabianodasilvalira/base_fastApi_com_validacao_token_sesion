-- --------------------------------------------------------
-- Servidor:                     127.0.0.1
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

-- Copiando estrutura para tabela public.alembic_version
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num" VARCHAR(32) NOT NULL,
	PRIMARY KEY ("version_num")
);

-- Copiando dados para a tabela public.alembic_version: 0 rows
/*!40000 ALTER TABLE "alembic_version" DISABLE KEYS */;
INSERT INTO "alembic_version" ("version_num") VALUES
	('474b82f714c9');
/*!40000 ALTER TABLE "alembic_version" ENABLE KEYS */;

-- Copiando estrutura para tabela public.categorias
CREATE TABLE IF NOT EXISTS "categorias" (
	"id" SERIAL NOT NULL,
	"nome" VARCHAR(100) NOT NULL,
	"descricao" TEXT NULL DEFAULT NULL,
	"imagem_url" VARCHAR(255) NULL DEFAULT NULL,
	"criado_em" TIMESTAMPTZ NULL DEFAULT now(),
	"atualizado_em" TIMESTAMPTZ NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	UNIQUE ("nome")
);

-- Copiando dados para a tabela public.categorias: 3 rows
/*!40000 ALTER TABLE "categorias" DISABLE KEYS */;
INSERT INTO "categorias" ("id", "nome", "descricao", "imagem_url", "criado_em", "atualizado_em") VALUES
	(1, 'Cervejass', 'Bebidas alcoólicas fermentadas, geralmente servidas geladas.', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTWh4A_KgrM_goJl06T9Pf6CeG1uvLaZS4QVg&s', '2025-05-27 08:19:16.208783-03', '2025-06-12 12:15:59.100367-03'),
	(2, 'Destilados', 'Bebidas alcoólicas obtidas por destilação, como vodka, whisky e cachaça.', 'https://forbes.com.br/wp-content/uploads/2019/12/ForbesLife_destilados_201219_Getty-Images.jpg', '2025-05-27 08:19:16.237336-03', '2025-06-12 12:16:24.088594-03'),
	(3, 'Tiragosto', 'Petiscos e acompanhamentos servidos com bebidas, como frituras, queijos e calabresa.', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS2FlpJ-I394mMEm6WIIB9sWWAWOXWFbKB9IQ&s', '2025-05-27 08:19:16.243888-03', '2025-06-12 12:16:44.156167-03');
/*!40000 ALTER TABLE "categorias" ENABLE KEYS */;

-- Copiando estrutura para tabela public.clientes
CREATE TABLE IF NOT EXISTS "clientes" (
	"id" SERIAL NOT NULL,
	"nome" VARCHAR NOT NULL,
	"telefone" VARCHAR NOT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"endereco" VARCHAR NULL DEFAULT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	"imagem_url" VARCHAR(255) NULL DEFAULT NULL,
	"saldo_credito" NUMERIC(10,2) NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	KEY ("imagem_url"),
	KEY ("nome"),
	KEY ("telefone")
);

-- Copiando dados para a tabela public.clientes: 4 rows
/*!40000 ALTER TABLE "clientes" DISABLE KEYS */;
INSERT INTO "clientes" ("id", "nome", "telefone", "observacoes", "endereco", "created_at", "updated_at", "imagem_url", "saldo_credito") VALUES
	(1, 'João da Silva', '31999991234', 'Cliente frequente, prefere pagar no débito.', 'Rua das Flores, 123 - Centro', NULL, '2025-06-12 08:38:35.564816', NULL, NULL),
	(4, 'Ana Paula Lima', '31966664321', 'Cliente VIP. Tem saldo de crédito registrado.', 'Rua do Ouro, 101 - Savassi', NULL, '2025-06-12 08:38:42.072139', NULL, NULL),
	(8, 'fabiano liras', '88888888888', 'teste', 'teste', '2025-06-12 08:50:38.05089', '2025-06-12 08:53:24.018191', 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRpORocZ-UyfvfXOC-1mAAIq_YlWiLAoLMB1A&s', 0.00),
	(3, 'Carlos', '31977777890', 'Sempre vem em grupo, solicita comanda separada.', 'Rua das Palmeiras, 789 - Jardim América', NULL, '2025-06-12 11:24:50.188623', NULL, NULL),
	(2, 'Maria Oliveira', '31988885678', 'Gosta de tiragostos e cerveja artesanal.', 'Av. Brasil, 456 - Bairro São Pedro', NULL, '2025-06-12 11:39:35.527066', NULL, NULL);
/*!40000 ALTER TABLE "clientes" ENABLE KEYS */;

-- Copiando estrutura para tabela public.comandas
CREATE TABLE IF NOT EXISTS "comandas" (
	"id" SERIAL NOT NULL,
	"id_mesa" INTEGER NOT NULL,
	"id_cliente_associado" INTEGER NULL DEFAULT NULL,
	"status_comanda" UNKNOWN NOT NULL,
	"valor_total_calculado" NUMERIC(10,2) NOT NULL,
	"percentual_taxa_servico" NUMERIC(5,2) NOT NULL,
	"valor_taxa_servico" NUMERIC(10,2) NOT NULL,
	"valor_desconto" NUMERIC(10,2) NOT NULL,
	"valor_final_comanda" NUMERIC(10,2) NOT NULL,
	"valor_pago" NUMERIC(10,2) NOT NULL,
	"valor_fiado" NUMERIC(10,2) NOT NULL,
	"valor_credito_usado" NUMERIC(10,2) NOT NULL,
	"motivo_cancelamento" TEXT NULL DEFAULT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"qr_code_comanda_hash" VARCHAR NULL DEFAULT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	UNIQUE ("qr_code_comanda_hash"),
	CONSTRAINT "comandas_id_cliente_associado_fkey" FOREIGN KEY ("id_cliente_associado") REFERENCES "clientes" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "comandas_id_mesa_fkey" FOREIGN KEY ("id_mesa") REFERENCES "mesas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.comandas: 3 rows
/*!40000 ALTER TABLE "comandas" DISABLE KEYS */;
INSERT INTO "comandas" ("id", "id_mesa", "id_cliente_associado", "status_comanda", "valor_total_calculado", "percentual_taxa_servico", "valor_taxa_servico", "valor_desconto", "valor_final_comanda", "valor_pago", "valor_fiado", "valor_credito_usado", "motivo_cancelamento", "observacoes", "qr_code_comanda_hash", "created_at", "updated_at") VALUES
	(1, 1, 1, 'ABERTA', 0.00, 10.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, NULL, 'mesa do joao', 'b99d5121-b41c-4742-8c12-6765ea654292', '2025-06-12 08:17:29.606087', '2025-06-12 08:17:29.606087'),
	(2, 2, 2, 'ABERTA', 0.00, 10.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, NULL, 'mesa da maria', '56ce7f2b-35d7-4124-8457-547f229a519e', '2025-06-12 08:17:42.403723', '2025-06-12 08:17:42.403723'),
	(3, 3, 3, 'ABERTA', 0.00, 10.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, NULL, 'mesa do carlos', '1bc30886-c28d-4ad3-9a48-e4523efd40bc', '2025-06-12 08:22:01.067865', '2025-06-12 08:22:01.067865');
/*!40000 ALTER TABLE "comandas" ENABLE KEYS */;

-- Copiando estrutura para tabela public.fiados
CREATE TABLE IF NOT EXISTS "fiados" (
	"id" SERIAL NOT NULL,
	"id_comanda" INTEGER NOT NULL,
	"id_cliente" INTEGER NOT NULL,
	"id_usuario_registrou" INTEGER NULL DEFAULT NULL,
	"valor_original" NUMERIC(10,2) NOT NULL,
	"valor_devido" NUMERIC(10,2) NOT NULL,
	"status_fiado" UNKNOWN NOT NULL,
	"data_vencimento" DATE NULL DEFAULT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"data_registro" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "fiados_id_cliente_fkey" FOREIGN KEY ("id_cliente") REFERENCES "clientes" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "fiados_id_comanda_fkey" FOREIGN KEY ("id_comanda") REFERENCES "comandas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "fiados_id_usuario_registrou_fkey" FOREIGN KEY ("id_usuario_registrou") REFERENCES "users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.fiados: 0 rows
/*!40000 ALTER TABLE "fiados" DISABLE KEYS */;
INSERT INTO "fiados" ("id", "id_comanda", "id_cliente", "id_usuario_registrou", "valor_original", "valor_devido", "status_fiado", "data_vencimento", "observacoes", "data_registro", "updated_at") VALUES
	(1, 1, 2, 1, 150.00, 0.00, 'PAGO_TOTALMENTE', NULL, '
Pagamento de R$25.00 registrado em 12/06/2025: teste', '2025-06-12 08:51:46.105925', '2025-06-12 11:24:16.970391');
/*!40000 ALTER TABLE "fiados" ENABLE KEYS */;

-- Copiando estrutura para tabela public.itens_pedido
CREATE TABLE IF NOT EXISTS "itens_pedido" (
	"id" SERIAL NOT NULL,
	"id_pedido" INTEGER NOT NULL,
	"id_comanda" INTEGER NOT NULL,
	"id_produto" INTEGER NOT NULL,
	"quantidade" INTEGER NOT NULL,
	"preco_unitario" NUMERIC(10,2) NOT NULL,
	"preco_total" NUMERIC(10,2) NOT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"status" UNKNOWN NOT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "itens_pedido_id_comanda_fkey" FOREIGN KEY ("id_comanda") REFERENCES "comandas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "itens_pedido_id_pedido_fkey" FOREIGN KEY ("id_pedido") REFERENCES "pedidos" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "itens_pedido_id_produto_fkey" FOREIGN KEY ("id_produto") REFERENCES "produtos" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.itens_pedido: 0 rows
/*!40000 ALTER TABLE "itens_pedido" DISABLE KEYS */;
/*!40000 ALTER TABLE "itens_pedido" ENABLE KEYS */;

-- Copiando estrutura para tabela public.mesas
CREATE TABLE IF NOT EXISTS "mesas" (
	"id" SERIAL NOT NULL,
	"numero_identificador" VARCHAR NOT NULL,
	"capacidade" INTEGER NULL DEFAULT NULL,
	"status" UNKNOWN NOT NULL,
	"qr_code_hash" VARCHAR NULL DEFAULT NULL,
	"id_cliente_associado" INTEGER NULL DEFAULT NULL,
	"ativa_para_pedidos" BOOLEAN NOT NULL,
	"criado_em" TIMESTAMPTZ NULL DEFAULT now(),
	"atualizado_em" TIMESTAMPTZ NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	UNIQUE ("numero_identificador"),
	UNIQUE ("qr_code_hash"),
	CONSTRAINT "mesas_id_cliente_associado_fkey" FOREIGN KEY ("id_cliente_associado") REFERENCES "clientes" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.mesas: 0 rows
/*!40000 ALTER TABLE "mesas" DISABLE KEYS */;
INSERT INTO "mesas" ("id", "numero_identificador", "capacidade", "status", "qr_code_hash", "id_cliente_associado", "ativa_para_pedidos", "criado_em", "atualizado_em") VALUES
	(1, '01', 4, 'DISPONIVEL', 'hash_qr_01', 1, 'true', '2025-05-27 08:20:10.094521-03', '2025-06-12 12:22:59.376774-03'),
	(2, '02', 4, 'DISPONIVEL', 'hash_qr_02', 2, 'true', '2025-05-27 08:20:10.094521-03', '2025-06-12 12:23:06.766853-03'),
	(4, '03', 4, 'DISPONIVEL', 'hash_qr_04', 4, 'true', '2025-05-27 08:20:10.094521-03', '2025-06-12 12:23:14.606879-03'),
	(3, '04', 2, 'OCUPADA', 'hash_qr_03', 3, 'true', '2025-05-27 08:20:10.094521-03', '2025-06-12 12:23:22.026999-03');
/*!40000 ALTER TABLE "mesas" ENABLE KEYS */;

-- Copiando estrutura para tabela public.pagamentos
CREATE TABLE IF NOT EXISTS "pagamentos" (
	"id" SERIAL NOT NULL,
	"id_comanda" INTEGER NOT NULL,
	"id_cliente" INTEGER NULL DEFAULT NULL,
	"id_usuario_registrou" INTEGER NULL DEFAULT NULL,
	"id_venda" INTEGER NULL DEFAULT NULL,
	"id_pedido" INTEGER NULL DEFAULT NULL,
	"valor_pago" NUMERIC(10,2) NOT NULL,
	"metodo_pagamento" UNKNOWN NOT NULL,
	"status_pagamento" UNKNOWN NOT NULL,
	"detalhes_transacao" VARCHAR NULL DEFAULT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"data_pagamento" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "pagamentos_id_cliente_fkey" FOREIGN KEY ("id_cliente") REFERENCES "clientes" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pagamentos_id_comanda_fkey" FOREIGN KEY ("id_comanda") REFERENCES "comandas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pagamentos_id_pedido_fkey" FOREIGN KEY ("id_pedido") REFERENCES "pedidos" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pagamentos_id_usuario_registrou_fkey" FOREIGN KEY ("id_usuario_registrou") REFERENCES "users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pagamentos_id_venda_fkey" FOREIGN KEY ("id_venda") REFERENCES "vendas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.pagamentos: 0 rows
/*!40000 ALTER TABLE "pagamentos" DISABLE KEYS */;
/*!40000 ALTER TABLE "pagamentos" ENABLE KEYS */;

-- Copiando estrutura para tabela public.password_reset_tokens
CREATE TABLE IF NOT EXISTS "password_reset_tokens" (
	"id" SERIAL NOT NULL,
	"user_id" INTEGER NOT NULL,
	"token" VARCHAR NOT NULL,
	"is_active" BOOLEAN NULL DEFAULT NULL,
	"expires_at" TIMESTAMP NOT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	UNIQUE ("token"),
	CONSTRAINT "password_reset_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON UPDATE NO ACTION ON DELETE CASCADE
);

-- Copiando dados para a tabela public.password_reset_tokens: 0 rows
/*!40000 ALTER TABLE "password_reset_tokens" DISABLE KEYS */;
INSERT INTO "password_reset_tokens" ("id", "user_id", "token", "is_active", "expires_at", "created_at") VALUES
	(1, 2, '_SsaBN5Zl8mcwkKmupXEsRquA-CtKo_1FysECzteh5Q', 'true', '2025-06-11 11:24:22.085446', '2025-06-11 11:14:22.087617'),
	(2, 2, 'EbIjpZVdn9uAx0nJZtd6xGC5sP3aIuLMWoh8VFRHFmo', 'true', '2025-06-11 11:26:54.867827', '2025-06-11 11:16:54.869863'),
	(3, 2, 'K1gF3hG-tXstpc7TYDL8sgmhnxtea6GKjgMjsZFjRx4', 'true', '2025-06-11 11:28:28.227431', '2025-06-11 11:18:28.228432'),
	(4, 2, 'cuTlVc-1wuF48YOP8j1iaPvCjJNDv19uOo7kOLOIKbU', 'true', '2025-06-11 11:28:46.440993', '2025-06-11 11:18:46.442'),
	(5, 2, 'wnOgoxBD0fQq48gjSkb5GglKwwalqtGdb9Railp5zwo', 'true', '2025-06-11 11:34:06.399617', '2025-06-11 11:24:06.400814'),
	(6, 2, 'VnV3OPpqIBXfZZBvzxWtZZwfLhd0aeJCwd3TI2VxjeQ', 'true', '2025-06-11 11:34:41.710271', '2025-06-11 11:24:41.712271'),
	(7, 2, 'kLoXH5wT8ZxvgqXXZmCmPCpvmEF9kyOzs3PLfPFb7I0', 'true', '2025-06-11 11:35:03.388552', '2025-06-11 11:25:03.390587'),
	(8, 2, 'uQtWvDLEbylidRaWl65UXojwX2cpp-0WNZFmD8fhlqE', 'true', '2025-06-11 11:35:16.883817', '2025-06-11 11:25:16.883817'),
	(9, 2, 'XlELJAh6wglX5qw13YwtZQ5WwQWZAsGAyldJ92rzrNY', 'true', '2025-06-11 11:36:26.779803', '2025-06-11 11:26:26.780802'),
	(10, 2, 'dWd8RR9ejLgXZvgr2qaOZU1gLe-PRn7SIAcx_y0C7pg', 'true', '2025-06-11 11:42:53.770608', '2025-06-11 11:32:53.773145'),
	(11, 2, 'GpBFUEkcaHLQCu5qVrFCge0rzH5lw1fLZb6mcF78R1U', 'true', '2025-06-11 11:45:27.228938', '2025-06-11 11:35:27.231443'),
	(12, 2, 'D4_bYqYov-8L0BKyrjdlA4y_pVrA8NFOmhyjj0s-xDs', 'true', '2025-06-11 11:47:17.825486', '2025-06-11 11:37:17.825486'),
	(13, 2, '1YRW0At8lP-eqxvVfw7mmu6gk7yDBsfg0CZA8ZM2n9Y', 'true', '2025-06-11 11:49:46.095995', '2025-06-11 11:39:46.107391'),
	(14, 2, 'hTCy5nwj99IQS5S0KHigdWuO-jmYIAczyzMx972IlFA', 'true', '2025-06-11 11:50:37.066708', '2025-06-11 11:40:37.067846'),
	(15, 2, 'Yt9gctKGjwV4ewkeBLwVetxSe9ETmPBG_tRhwyzHtyo', 'true', '2025-06-11 11:51:35.368537', '2025-06-11 11:41:35.368537'),
	(16, 2, 's1RsBn0cUeeUs3dXebNEpwVhtPCwdliJ4FDTNnJRWTU', 'true', '2025-06-11 11:52:58.522701', '2025-06-11 11:42:58.522701'),
	(17, 2, 'WpMoZHfVV2EivV7s3pCEVGaqIpV-aBGM7xbqTi5yLLE', 'true', '2025-06-11 11:54:38.162968', '2025-06-11 11:44:38.162968'),
	(18, 2, 'dcds4jf8nUdAicdNmv84HwE0KlD4KVxaolb7zvc58gc', 'true', '2025-06-11 11:55:58.950922', '2025-06-11 11:45:58.950922'),
	(19, 2, 'pxHcpIJINvIXGYz0vwzCeKh_EMXE2hZimJ6T_m_4PlA', 'true', '2025-06-11 12:01:04.741822', '2025-06-11 11:51:04.741822'),
	(20, 2, 'AIfrkRYX7iQNPHSfyqgLZ7hWgBK3-ZuUhiUN_bmXhmw', 'false', '2025-06-11 13:18:03.586589', '2025-06-11 13:08:03.587588');
/*!40000 ALTER TABLE "password_reset_tokens" ENABLE KEYS */;

-- Copiando estrutura para tabela public.pedidos
CREATE TABLE IF NOT EXISTS "pedidos" (
	"id" SERIAL NOT NULL,
	"id_comanda" INTEGER NOT NULL,
	"id_usuario_registrou" INTEGER NULL DEFAULT NULL,
	"mesa_id" INTEGER NULL DEFAULT NULL,
	"tipo_pedido" UNKNOWN NOT NULL,
	"status_geral_pedido" UNKNOWN NOT NULL,
	"observacoes_pedido" TEXT NULL DEFAULT NULL,
	"motivo_cancelamento" TEXT NULL DEFAULT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "pedidos_id_comanda_fkey" FOREIGN KEY ("id_comanda") REFERENCES "comandas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pedidos_id_usuario_registrou_fkey" FOREIGN KEY ("id_usuario_registrou") REFERENCES "users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "pedidos_mesa_id_fkey" FOREIGN KEY ("mesa_id") REFERENCES "mesas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.pedidos: 0 rows
/*!40000 ALTER TABLE "pedidos" DISABLE KEYS */;
/*!40000 ALTER TABLE "pedidos" ENABLE KEYS */;

-- Copiando estrutura para tabela public.produtos
CREATE TABLE IF NOT EXISTS "produtos" (
	"id" SERIAL NOT NULL,
	"nome" VARCHAR NOT NULL,
	"descricao" TEXT NULL DEFAULT NULL,
	"preco_unitario" NUMERIC(10,2) NOT NULL,
	"disponivel" BOOLEAN NOT NULL,
	"imagem_url" VARCHAR(255) NULL DEFAULT NULL,
	"categoria_id" INTEGER NULL DEFAULT NULL,
	"criado_em" TIMESTAMPTZ NOT NULL DEFAULT now(),
	"atualizado_em" TIMESTAMPTZ NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("categoria_id"),
	KEY ("id"),
	KEY ("nome"),
	CONSTRAINT "produtos_categoria_id_fkey" FOREIGN KEY ("categoria_id") REFERENCES "categorias" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.produtos: 0 rows
/*!40000 ALTER TABLE "produtos" DISABLE KEYS */;
INSERT INTO "produtos" ("id", "nome", "descricao", "preco_unitario", "disponivel", "imagem_url", "categoria_id", "criado_em", "atualizado_em") VALUES
	(1, 'Skol', 'Cerveja leve e refrescante', 5.50, 'true', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Skol_logo.svg/1200px-Skol_logo.svg.png', 1, '2025-05-27 08:21:19.734175-03', NULL),
	(2, 'Brahma', 'Cerveja tradicional brasileira', 5.80, 'true', 'https://upload.wikimedia.org/wikipedia/commons/4/44/Brahma_logo.svg', 1, '2025-05-27 08:21:19.734175-03', NULL),
	(3, 'Heineken', 'Cerveja premium importada', 7.20, 'true', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Heineken_logo.svg/1200px-Heineken_logo.svg.png', 1, '2025-05-27 08:21:19.734175-03', NULL),
	(4, 'Stella Artois', 'Cerveja belga clássica', 8.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/7/79/Stella_Artois_logo.svg', 1, '2025-05-27 08:21:19.734175-03', NULL),
	(5, 'Budweiser', 'Cerveja americana saborosa', 6.50, 'true', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Budweiser_logo.svg/1200px-Budweiser_logo.svg.png', 1, '2025-05-27 08:21:19.734175-03', NULL),
	(6, 'Whisky Johnnie Walker', 'Whisky escocês blended', 120.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/8/8c/Johnnie_Walker_Black_Label_1L_bottle.jpg', 2, '2025-05-27 08:21:19.745414-03', NULL),
	(7, 'Vodka Absolut', 'Vodka sueca pura e suave', 90.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Absolut_Vodka_bottle.jpg', 2, '2025-05-27 08:21:19.745414-03', NULL),
	(8, 'Cachaça 51', 'Cachaça brasileira tradicional', 30.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/1/1e/Cachaca_51.jpg', 2, '2025-05-27 08:21:19.745414-03', NULL),
	(9, 'Gin Tanqueray', 'Gin premium com sabor intenso', 110.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/0/0c/Tanqueray_Gin_Bottle.jpg', 2, '2025-05-27 08:21:19.745414-03', NULL),
	(10, 'Rum Bacardi', 'Rum clássico para drinks', 85.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/7/7f/Bacardi_Light_Rum_750ml_Bottle.jpg', 2, '2025-05-27 08:21:19.745414-03', NULL),
	(11, 'Batata Frita', 'Porção de batatas fritas crocantes', 15.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/6/68/Canadian_French_fries_with_mayo.jpg', 3, '2025-05-27 08:21:19.752207-03', NULL),
	(12, 'Azeitonas', 'Porção de azeitonas temperadas', 12.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/6/6a/Olives_mixed_01.jpg', 3, '2025-05-27 08:21:19.752207-03', NULL),
	(13, 'Amendoim', 'Amendoim torrado e salgado', 8.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/3/37/Peanuts-raw.jpg', 3, '2025-05-27 08:21:19.752207-03', NULL),
	(14, 'Calabresa Acebolada', 'Calabresa frita com cebola', 20.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/0/0f/Calabresa_e_acebolada.jpg', 3, '2025-05-27 08:21:19.752207-03', NULL),
	(15, 'Pastel', 'Pastel frito com recheio variado', 10.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/6/6d/Pastel.jpg', 3, '2025-05-27 08:21:19.752207-03', NULL);
/*!40000 ALTER TABLE "produtos" ENABLE KEYS */;

-- Copiando estrutura para tabela public.refresh_tokens
CREATE TABLE IF NOT EXISTS "refresh_tokens" (
	"id" SERIAL NOT NULL,
	"user_id" INTEGER NOT NULL,
	"token" VARCHAR NOT NULL,
	"expires_at" TIMESTAMP NOT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"is_active" BOOLEAN NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	UNIQUE ("token"),
	CONSTRAINT "refresh_tokens_user_id_fkey" FOREIGN KEY ("user_id") REFERENCES "users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.refresh_tokens: 0 rows
/*!40000 ALTER TABLE "refresh_tokens" DISABLE KEYS */;
INSERT INTO "refresh_tokens" ("id", "user_id", "token", "expires_at", "created_at", "is_active") VALUES
	(1, 1, 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbkBleGFtcGxlLmNvbSIsInVzZXJfaWQiOiIxIiwiZXhwIjoxNzUwMzMxNTExLCJ0eXBlIjoicmVmcmVzaCJ9.RNoQfaAzOPXLZYyhCjfrvQTkSLtF7cT4MQTn79bpUdE', '2025-06-19 11:11:51.942788', '2025-06-12 08:11:51.443876', 'true');
/*!40000 ALTER TABLE "refresh_tokens" ENABLE KEYS */;

-- Copiando estrutura para tabela public.users
CREATE TABLE IF NOT EXISTS "users" (
	"id" SERIAL NOT NULL,
	"email" VARCHAR NOT NULL,
	"username" VARCHAR NULL DEFAULT NULL,
	"hashed_password" VARCHAR NOT NULL,
	"first_name" VARCHAR NULL DEFAULT NULL,
	"last_name" VARCHAR NULL DEFAULT NULL,
	"phone" VARCHAR NULL DEFAULT NULL,
	"imagem_url" VARCHAR(255) NULL DEFAULT NULL,
	"is_verified" BOOLEAN NULL DEFAULT NULL,
	"is_active" BOOLEAN NULL DEFAULT NULL,
	"is_superuser" BOOLEAN NULL DEFAULT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	UNIQUE ("phone"),
	UNIQUE ("email"),
	KEY ("id"),
	KEY ("imagem_url"),
	UNIQUE ("username")
);

-- Copiando dados para a tabela public.users: 0 rows
/*!40000 ALTER TABLE "users" DISABLE KEYS */;
INSERT INTO "users" ("id", "email", "username", "hashed_password", "first_name", "last_name", "phone", "imagem_url", "is_verified", "is_active", "is_superuser", "created_at", "updated_at") VALUES
	(1, 'admin@example.com', 'admin', '$2b$12$pC5CAuIOZ5pwM8OT3720/OTtayto72mtQ8ctrRS2hfRUyWv7M89ui', 'Administrador', NULL, NULL, NULL, 'false', 'true', 'true', '2025-06-11 10:41:31.734027', '2025-06-11 10:41:31.734027'),
	(2, 'fabianodaslira@gmail.com', 'fabiano', '$2b$12$dw4y3cnotSQvBt8ccf01X.uLrb.DU3hU3Osa9S7jDxTcNI1hqzA6W', 'Administrador', NULL, NULL, NULL, 'false', 'true', 'true', '2025-06-11 10:41:31.734027', '2025-06-11 13:16:07.771654');
/*!40000 ALTER TABLE "users" ENABLE KEYS */;

-- Copiando estrutura para tabela public.vendas
CREATE TABLE IF NOT EXISTS "vendas" (
	"id" SERIAL NOT NULL,
	"valor_total" NUMERIC(10,2) NOT NULL,
	"data_venda" DATE NOT NULL,
	"usuario_id" INTEGER NOT NULL,
	"cliente_id" INTEGER NULL DEFAULT NULL,
	"comanda_id" INTEGER NULL DEFAULT NULL,
	"criado_em" TIMESTAMPTZ NULL DEFAULT now(),
	"atualizado_em" TIMESTAMPTZ NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "vendas_cliente_id_fkey" FOREIGN KEY ("cliente_id") REFERENCES "clientes" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "vendas_comanda_id_fkey" FOREIGN KEY ("comanda_id") REFERENCES "comandas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "vendas_usuario_id_fkey" FOREIGN KEY ("usuario_id") REFERENCES "users" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.vendas: 0 rows
/*!40000 ALTER TABLE "vendas" DISABLE KEYS */;
/*!40000 ALTER TABLE "vendas" ENABLE KEYS */;

-- Copiando estrutura para tabela public.venda_produto
CREATE TABLE IF NOT EXISTS "venda_produto" (
	"id_venda" INTEGER NOT NULL,
	"id_produto" INTEGER NOT NULL,
	"quantidade_vendida" INTEGER NOT NULL,
	"preco_unitario_na_venda" DOUBLE PRECISION NOT NULL,
	PRIMARY KEY ("id_venda", "id_produto"),
	CONSTRAINT "venda_produto_id_produto_fkey" FOREIGN KEY ("id_produto") REFERENCES "produtos" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "venda_produto_id_venda_fkey" FOREIGN KEY ("id_venda") REFERENCES "vendas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Copiando dados para a tabela public.venda_produto: 0 rows
/*!40000 ALTER TABLE "venda_produto" DISABLE KEYS */;
/*!40000 ALTER TABLE "venda_produto" ENABLE KEYS */;

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
