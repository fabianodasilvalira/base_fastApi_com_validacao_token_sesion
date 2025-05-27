

-- Copiando dados para a tabela public.categorias: 3 rows
/*!40000 ALTER TABLE "categorias" DISABLE KEYS */;
INSERT INTO "categorias" ("id", "nome", "descricao", "imagem_url", "criado_em", "atualizado_em") VALUES
	(1, 'Cervejas', 'Bebidas alcoólicas fermentadas, geralmente servidas geladas.', 'https://example.com/imagens/cervejas.jpg', '2025-05-27 11:19:16.208783+00', NULL),
	(2, 'Destilados', 'Bebidas alcoólicas obtidas por destilação, como vodka, whisky e cachaça.', 'https://example.com/imagens/destilados.jpg', '2025-05-27 11:19:16.237336+00', NULL),
	(3, 'Tiragosto', 'Petiscos e acompanhamentos servidos com bebidas, como frituras, queijos e calabresa.', 'https://example.com/imagens/tiragosto.jpg', '2025-05-27 11:19:16.243888+00', NULL);
/*!40000 ALTER TABLE "categorias" ENABLE KEYS */;

-- Copiando dados para a tabela public.clientes: 4 rows
/*!40000 ALTER TABLE "clientes" DISABLE KEYS */;
INSERT INTO "clientes" ("id", "nome", "telefone", "observacoes", "endereco", "created_at", "updated_at", "imagem_url") VALUES
	(1, 'João da Silva', '(31) 99999-1234', 'Cliente frequente, prefere pagar no débito.', 'Rua das Flores, 123 - Centro', NULL, NULL, 'https://example.com/imagens/joao.jpg'),
	(2, 'Maria Oliveira', '(31) 98888-5678', 'Gosta de tiragostos e cerveja artesanal.', 'Av. Brasil, 456 - Bairro São Pedro', NULL, NULL, 'https://example.com/imagens/maria.jpg'),
	(3, 'Carlos Souza', '(31) 97777-7890', 'Sempre vem em grupo, solicita comanda separada.', 'Rua das Palmeiras, 789 - Jardim América', NULL, NULL, 'https://example.com/imagens/carlos.jpg'),
	(4, 'Ana Paula Lima', '(31) 96666-4321', 'Cliente VIP. Tem saldo de crédito registrado.', 'Rua do Ouro, 101 - Savassi', NULL, NULL, 'https://example.com/imagens/ana.jpg');
/*!40000 ALTER TABLE "clientes" ENABLE KEYS */;




-- Copiando dados para a tabela public.mesas: 4 rows
/*!40000 ALTER TABLE "mesas" DISABLE KEYS */;
INSERT INTO "mesas" ("id", "numero_identificador", "capacidade", "status", "qr_code_hash", "id_cliente_associado", "ativa_para_pedidos", "criado_em", "atualizado_em") VALUES
	(1, 'MESA-01', 4, 'DISPONIVEL', 'hash_qr_01', 1, 'true', '2025-05-27 11:20:10.094521+00', NULL),
	(2, 'MESA-02', 6, 'DISPONIVEL', 'hash_qr_02', 2, 'true', '2025-05-27 11:20:10.094521+00', NULL),
	(3, 'MESA-03', 2, 'DISPONIVEL', 'hash_qr_03', 3, 'true', '2025-05-27 11:20:10.094521+00', NULL),
	(4, 'MESA-04', 8, 'DISPONIVEL', 'hash_qr_04', 4, 'true', '2025-05-27 11:20:10.094521+00', NULL);
/*!40000 ALTER TABLE "mesas" ENABLE KEYS */;




-- Copiando dados para a tabela public.produtos: 15 rows
/*!40000 ALTER TABLE "produtos" DISABLE KEYS */;
INSERT INTO "produtos" ("id", "nome", "descricao", "preco_unitario", "disponivel", "imagem_url", "criado_em", "atualizado_em", "categoria_id") VALUES
	(1, 'Skol', 'Cerveja leve e refrescante', 5.50, 'true', 'https://upload.wikimedia.org/wikipedia/commons/thumb/3/31/Skol_logo.svg/1200px-Skol_logo.svg.png', '2025-05-27 11:21:19.734175+00', NULL, 1),
	(2, 'Brahma', 'Cerveja tradicional brasileira', 5.80, 'true', 'https://upload.wikimedia.org/wikipedia/commons/4/44/Brahma_logo.svg', '2025-05-27 11:21:19.734175+00', NULL, 1),
	(3, 'Heineken', 'Cerveja premium importada', 7.20, 'true', 'https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Heineken_logo.svg/1200px-Heineken_logo.svg.png', '2025-05-27 11:21:19.734175+00', NULL, 1),
	(4, 'Stella Artois', 'Cerveja belga clássica', 8.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/7/79/Stella_Artois_logo.svg', '2025-05-27 11:21:19.734175+00', NULL, 1),
	(5, 'Budweiser', 'Cerveja americana saborosa', 6.50, 'true', 'https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Budweiser_logo.svg/1200px-Budweiser_logo.svg.png', '2025-05-27 11:21:19.734175+00', NULL, 1),
	(6, 'Whisky Johnnie Walker', 'Whisky escocês blended', 120.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/8/8c/Johnnie_Walker_Black_Label_1L_bottle.jpg', '2025-05-27 11:21:19.745414+00', NULL, 2),
	(7, 'Vodka Absolut', 'Vodka sueca pura e suave', 90.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/3/3e/Absolut_Vodka_bottle.jpg', '2025-05-27 11:21:19.745414+00', NULL, 2),
	(8, 'Cachaça 51', 'Cachaça brasileira tradicional', 30.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/1/1e/Cachaca_51.jpg', '2025-05-27 11:21:19.745414+00', NULL, 2),
	(9, 'Gin Tanqueray', 'Gin premium com sabor intenso', 110.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/0/0c/Tanqueray_Gin_Bottle.jpg', '2025-05-27 11:21:19.745414+00', NULL, 2),
	(10, 'Rum Bacardi', 'Rum clássico para drinks', 85.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/7/7f/Bacardi_Light_Rum_750ml_Bottle.jpg', '2025-05-27 11:21:19.745414+00', NULL, 2),
	(11, 'Batata Frita', 'Porção de batatas fritas crocantes', 15.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/6/68/Canadian_French_fries_with_mayo.jpg', '2025-05-27 11:21:19.752207+00', NULL, 3),
	(12, 'Azeitonas', 'Porção de azeitonas temperadas', 12.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/6/6a/Olives_mixed_01.jpg', '2025-05-27 11:21:19.752207+00', NULL, 3),
	(13, 'Amendoim', 'Amendoim torrado e salgado', 8.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/3/37/Peanuts-raw.jpg', '2025-05-27 11:21:19.752207+00', NULL, 3),
	(14, 'Calabresa Acebolada', 'Calabresa frita com cebola', 20.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/0/0f/Calabresa_e_acebolada.jpg', '2025-05-27 11:21:19.752207+00', NULL, 3),
	(15, 'Pastel', 'Pastel frito com recheio variado', 10.00, 'true', 'https://upload.wikimedia.org/wikipedia/commons/6/6d/Pastel.jpg', '2025-05-27 11:21:19.752207+00', NULL, 3);
/*!40000 ALTER TABLE "produtos" ENABLE KEYS */;

