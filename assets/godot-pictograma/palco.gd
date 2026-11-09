extends Node2D

var frames: Array
var index := 0
var raster: ImageTexture
var size: Vector2
var archivo: FontVariation
var atkinson: FontFile

func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1:
		push_error("Informe o caminho dos quadros.")
		get_tree().quit(2)
		return
	var data = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not data is Dictionary or not data.get("frames") is Array or data.frames.is_empty():
		push_error("Arquivo de quadros inválido.")
		get_tree().quit(2)
		return
	frames = data.frames
	size = Vector2(data.size[0], data.size[1])
	get_viewport().content_scale_size = Vector2i(size)
	atkinson = FontFile.new()
	archivo = FontVariation.new()
	var display_font := FontFile.new()
	if atkinson.load_dynamic_font("res://Atkinson-Bold.ttf") != OK or display_font.load_dynamic_font("res://Archivo.ttf") != OK:
		push_error("Fontes do Pictograma ausentes.")
		get_tree().quit(2)
		return
	archivo.base_font = display_font
	var text_server := TextServerManager.get_primary_interface()
	archivo.variation_opentype = {text_server.name_to_tag("wght"): 800, text_server.name_to_tag("wdth"): 80}
	_prepare()
	RenderingServer.frame_post_draw.connect(_advance)

func _prepare() -> void:
	var image := Image.new()
	if image.load_svg_from_string(frames[index].svg) != OK:
		push_error("SVG inválido no quadro %d." % index)
		get_tree().quit(2)
		return
	raster = ImageTexture.create_from_image(image)
	queue_redraw()

func _draw() -> void:
	if raster == null:
		return
	draw_texture_rect(raster, Rect2(Vector2.ZERO, size), false)
	for part in frames[index].text:
		var font: Font = archivo if part.display else atkinson
		var pixels := maxi(1, roundi(part.font_size))
		var natural := font.get_string_size(part.value, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels).x
		var stretch := float(part.advance) / natural if natural > 0.0 and part.advance > 0.0 else 1.0
		var m: Array = part.matrix
		var transform := Transform2D(Vector2(m[0], m[1]), Vector2(m[2], m[3]), Vector2(m[4], m[5]))
		draw_set_transform_matrix(transform * Transform2D(0.0, Vector2(stretch, 1.0), 0.0, Vector2(part.x, part.y)))
		var ink := Color.from_string(part.color, Color.WHITE)
		ink.a *= float(part.opacity)
		draw_string(font, Vector2.ZERO, part.value, HORIZONTAL_ALIGNMENT_LEFT, -1, pixels, ink)
	draw_set_transform_matrix(Transform2D.IDENTITY)

func _advance() -> void:
	index += 1
	if index >= frames.size():
		RenderingServer.frame_post_draw.disconnect(_advance)
	else:
		call_deferred("_prepare")
