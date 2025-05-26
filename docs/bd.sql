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

-- Copiando estrutura para tabela public.alembic_version
CREATE TABLE IF NOT EXISTS "alembic_version" (
	"version_num" VARCHAR(32) NOT NULL,
	PRIMARY KEY ("version_num")
);

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

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
	PRIMARY KEY ("id"),
	KEY ("id"),
	KEY ("imagem_url"),
	KEY ("nome"),
	KEY ("telefone")
);

-- Exportação de dados foi desmarcado.

-- Copiando estrutura para tabela public.comandas
CREATE TABLE IF NOT EXISTS "comandas" (
	"id" SERIAL NOT NULL,
	"id_mesa" INTEGER NOT NULL,
	"id_cliente_associado" INTEGER NULL DEFAULT NULL,
	"status_comanda" UNKNOWN NOT NULL,
	"valor_total_calculado" NUMERIC(10,2) NOT NULL,
	"valor_pago" NUMERIC(10,2) NOT NULL,
	"valor_fiado" NUMERIC(10,2) NOT NULL,
	"percentual_taxa_servico" NUMERIC(10,2) NOT NULL,
	"motivo_cancelamento" TEXT NULL DEFAULT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"qr_code_comanda_hash" VARCHAR NULL DEFAULT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	"valor_taxa_servico" NUMERIC(10,2) NOT NULL,
	"valor_desconto" NUMERIC(10,2) NOT NULL,
	UNIQUE ("qr_code_comanda_hash"),
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "comandas_id_cliente_associado_fkey" FOREIGN KEY ("id_cliente_associado") REFERENCES "clientes" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "comandas_id_mesa_fkey" FOREIGN KEY ("id_mesa") REFERENCES "mesas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

-- Copiando estrutura para tabela public.itens_pedido
CREATE TABLE IF NOT EXISTS "itens_pedido" (
	"id" SERIAL NOT NULL,
	"id_pedido" INTEGER NOT NULL,
	"id_comanda" INTEGER NOT NULL,
	"id_produto" INTEGER NOT NULL,
	"quantidade" INTEGER NOT NULL,
	"preco_unitario" NUMERIC(10,2) NOT NULL,
	"observacoes" TEXT NULL DEFAULT NULL,
	"status" UNKNOWN NOT NULL,
	"created_at" TIMESTAMP NULL DEFAULT NULL,
	"updated_at" TIMESTAMP NULL DEFAULT NULL,
	"preco_total" NUMERIC(10,2) NOT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	CONSTRAINT "itens_pedido_id_comanda_fkey" FOREIGN KEY ("id_comanda") REFERENCES "comandas" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "itens_pedido_id_pedido_fkey" FOREIGN KEY ("id_pedido") REFERENCES "pedidos" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION,
	CONSTRAINT "itens_pedido_id_produto_fkey" FOREIGN KEY ("id_produto") REFERENCES "produtos" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

-- Copiando estrutura para tabela public.produtos
CREATE TABLE IF NOT EXISTS "produtos" (
	"id" SERIAL NOT NULL,
	"nome" VARCHAR NOT NULL,
	"descricao" TEXT NULL DEFAULT NULL,
	"preco_unitario" NUMERIC(10,2) NOT NULL,
	"disponivel" BOOLEAN NULL DEFAULT NULL,
	"imagem_url" VARCHAR(255) NULL DEFAULT NULL,
	"criado_em" TIMESTAMPTZ NULL DEFAULT now(),
	"atualizado_em" TIMESTAMPTZ NULL DEFAULT NULL,
	"categoria_id" INTEGER NULL DEFAULT NULL,
	PRIMARY KEY ("id"),
	KEY ("id"),
	KEY ("imagem_url"),
	KEY ("nome"),
	CONSTRAINT "produtos_categoria_id_fkey" FOREIGN KEY ("categoria_id") REFERENCES "categorias" ("id") ON UPDATE NO ACTION ON DELETE NO ACTION
);

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

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

-- Exportação de dados foi desmarcado.

/*!40103 SET TIME_ZONE=IFNULL(@OLD_TIME_ZONE, 'system') */;
/*!40101 SET SQL_MODE=IFNULL(@OLD_SQL_MODE, '') */;
/*!40014 SET FOREIGN_KEY_CHECKS=IFNULL(@OLD_FOREIGN_KEY_CHECKS, 1) */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40111 SET SQL_NOTES=IFNULL(@OLD_SQL_NOTES, 1) */;
