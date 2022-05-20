# Snooker demo

import harfang as hg
import sys
from math import sin, cos, pi, atan2, sqrt
from sprites import *
from animations import *
import subprocess
import re

# Game vars
res_x, res_y = 1920, 1080

class Main:
	if len(sys.argv) >= 2:
		if sys.argv[1] == "--aaa":
			flag_AAA = True
		else:
			flag_AAA = False
	else:
		flag_AAA = False
	flag_start = False
	flag_gui = False

	mouse = None
	keyboard = None
	win = None

	state_observation_camera_distance = 0
	state_observation_camera_altitude = 0
	state_observation_camera_pitch = 0

	state_targeting_camera_distance = 0.75
	state_targeting_camera_altitude = 1.1
	state_targeting_camera_pitch = 15 / 180 * pi

	state_targeting_distance_range = [0.3, 1]
	state_targeting_altitude_range = [0.1, 0.3]
	shoot_level = 0.5
	impulse_range = [0.1, 6]

	resolution = hg.Vec2(res_x, res_y)
	balls = []
	balls_start_params = []
	sprites_display_list = []

	pool_table = None
	table_center = None
	stick = None
	stick_start_params = []

	stick_idle_params = [hg.Vec3(0.1770, 0.0465, 0.3803), hg.Vec3(hg.Deg(1.7962), hg.Deg(-92.6421), hg.Deg(59.4299))]
	stick_targeting_params = [[hg.Vec3(0, -0.03, 0.2), hg.Vec3(0, hg.Deg(-90), 0)], [hg.Vec3(0, -0.05, 0.5), hg.Vec3(0, hg.Deg(-90), 0)]]

	selector = None
	selector_offset_y = 54

	pipeline = None
	pipeline_res = None
	pipeline_aaa_config = None
	ipeline_aaa = None
	views = None
	render_data = None

	current_ball_hover = None

	current_state = None

	vs_decl = None

	sphere_ref = None
	collision_nodes = []
	scene = None
	scene_physics = None
	clocks = None
	physic_step = 0

	frame = 0
	timestep = 1 / 60
	ts = 0  # Timestamp (s)

	anim_camera_pos = None
	anim_camera_rot = None

	anim_stick_pos = None
	anim_stick_rot = None

	shoot_v = None
	shoot_p = None
	shoot_ball = None

	vtx_decl_lines = None
	physx_debug_lines_program = None


#

def display_physics_debug(vid):
	hg.SetViewRect(vid, 0, 0, int(Main.resolution.x), int(Main.resolution.y))
	cam = Main.scene.GetCurrentCamera()
	hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
	cam_mat = cam.GetTransform().GetWorld()
	view_matrix = hg.InverseFast(cam_mat)
	c = cam.GetCamera()
	projection_matrix = hg.ComputePerspectiveProjectionMatrix(c.GetZNear(), c.GetZFar(), hg.FovToZoomFactor(c.GetFov()), hg.Vec2(Main.resolution.x / Main.resolution.y, 1))
	hg.SetViewTransform(vid, view_matrix, projection_matrix)
	Main.scene_physics.RenderCollision(vid, Main.vtx_decl_lines, Main.physx_debug_lines_program, hg.ComputeRenderState(hg.BM_Opaque, hg.DT_Disabled, hg.FC_Disabled), 1)


def init_game():
	hg.InputInit()
	hg.WindowSystemInit()

	Main.win = hg.RenderInit('Snooker game', res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)
	hg.RenderReset(res_x, res_y, hg.RF_VSync | hg.RF_MSAA8X | hg.RF_MaxAnisotropy)

	# Setup assets folder
	hg.AddAssetsFolder("assets_compiled")

	# rendering pipeline
	shadow_map_resolution = 2048
	shadow_map_16bit = True
	Main.pipeline = hg.CreateForwardPipeline(shadow_map_resolution, shadow_map_16bit)
	Main.pipeline_res = hg.PipelineResources()

	# AAA pipeline
	Main.pipeline_aaa_config = hg.ForwardPipelineAAAConfig()
	Main.pipeline_aaa_config.motion_blur = 0.001
	Main.pipeline_aaa_config.temporal_aa_weight = 0.01
	Main.pipeline_aaa_config.sample_count = 1
	Main.pipeline_aaa = hg.CreateForwardPipelineAAAFromAssets("core", Main.pipeline_aaa_config, hg.BR_Equal, hg.BR_Equal)
	Main.views = hg.SceneForwardPipelinePassViewId()
	Main.render_data = hg.SceneForwardPipelineRenderData()

	# Setup inputs
	Main.mouse = hg.Mouse()
	Main.keyboard = hg.Keyboard()

	# load host scene
	Main.scene = hg.Scene()
	hg.LoadSceneFromAssets("pool/pool_Main_scene.scn", Main.scene, Main.pipeline_res, hg.GetForwardPipelineInfo())
	Main.balls.append(Main.scene.GetNode("ball_red"))
	Main.balls.append(Main.scene.GetNode("ball_white"))
	Main.balls.append(Main.scene.GetNode("ball_yellow"))
	Main.table_center = Main.scene.GetNode("table_center")
	Main.stick = Main.scene.GetNode("cue_stick")

	# Collision system:
	Main.vs_decl = hg.VertexLayout()
	Main.vs_decl.Begin()
	Main.vs_decl.Add(hg.A_Position, 3, hg.AT_Float)
	Main.vs_decl.Add(hg.A_Normal, 3, hg.AT_Uint8, True, True)
	Main.vs_decl.End()

	Main.scene_physics = hg.SceneBullet3Physics()
	Main.clocks = hg.SceneClocks()
	Main.physic_step = hg.time_from_sec_f(1 / 600)

	hg.SceneUpdateSystems(Main.scene, Main.clocks, hg.time_from_sec_f(1 / 60), Main.scene_physics, Main.physic_step, 10)
	Main.stick_start_params = [Main.stick.GetTransform().GetPos(), Main.stick.GetTransform().GetRot()]
	setup_collisions()

	# Setup camera:
	camera = Main.scene.GetNode("Camera")
	Main.scene.SetCurrentCamera(camera)
	hg.SceneUpdateSystems(Main.scene, Main.clocks, hg.time_from_sec_f(1 / 60), Main.scene_physics, Main.physic_step, 10)
	cam_pos = camera.GetTransform().GetPos()
	cam_rot = camera.GetTransform().GetRot()
	Main.state_observation_camera_pitch = cam_rot.x
	Main.state_observation_camera_altitude = cam_pos.y
	Main.state_observation_camera_distance = hg.Len((Main.table_center.GetTransform().GetPos() - cam_pos))

	# Load sprites
	Sprite.init_system()
	Main.selector = Sprite(128, 128, "sprites/selector.png")
	Main.selector.set_size(0.5)

	# Physics debug display
	Main.vtx_decl_lines = hg.VertexLayout()
	Main.vtx_decl_lines.Begin()
	Main.vtx_decl_lines.Add(hg.A_Position, 3, hg.AT_Float)
	Main.vtx_decl_lines.Add(hg.A_Color0, 3, hg.AT_Float)
	Main.vtx_decl_lines.End()
	Main.physx_debug_lines_program = hg.LoadProgramFromAssets("shaders/pos_rgb")


# Tools

def get_object_radius(object): #, pipeline_resources: hg.PipelineResources):
	_, mm = object.GetObject().GetMinMax(Main.pipeline_res)
	size = (mm.mx - mm.mn)
	return max(size.z,(max(size.x, size.y))) / 2


def get_screen_position(camera:hg.Node, point: hg.Vec3, resolution: hg.Vec2):
	cam = camera.GetCamera()
	view_state = hg.ComputePerspectiveViewState(camera.GetTransform().GetWorld(), cam.GetFov(), cam.GetZNear(), cam.GetZFar(), hg.ComputeAspectRatioX(resolution.x, resolution.y))
	flag, pos2d = hg.ProjectToScreenSpace(view_state.proj, view_state.view * point, resolution)
	if flag:
		return hg.Vec2(pos2d.x, pos2d.y)
	else:
		return None


def hover_objects_test(objects_list: list, camera: hg.Node, resolution: hg.Vec2, mouse_position: hg.Vec2):
	camera_pos = camera.GetTransform().GetPos()
	objects_list.sort(key = lambda x: hg.Len(hg.GetT(x.GetTransform().GetWorld()) - camera_pos))
	cam_aY = hg.GetY(camera.GetTransform().GetWorld())
	for object in objects_list:
		object_position = hg.GetT(object.GetTransform().GetWorld())
		object_screen_position = get_screen_position(camera, object_position, resolution)
		if object_screen_position is not None:
			object_radius = get_object_radius(object)
			object_bound_position = object_position + cam_aY * object_radius
			object_bound_screen_position = get_screen_position(camera, object_bound_position, resolution)
			if object_bound_screen_position is not None:
				object_screen_radius = hg.Len(object_bound_screen_position - object_screen_position)
				if hg.Len( mouse_position - object_screen_position) < object_screen_radius:
					return object
	return None


def compute_mouse_circular_pos(pos, target_pos, distance, ground_altitude):
	altitude = ground_altitude - target_pos.y
	dist2d = sqrt(pow(distance, 2) - pow(altitude, 2))
	v = pos - target_pos
	v.y = 0
	v = hg.Normalize(v)
	angle = atan2(v.z, v.x)
	mx = Main.mouse.DtX()
	angle -= mx / 200
	v.x, v.z = dist2d * cos(angle), dist2d * sin(angle)
	pos = target_pos + v
	pos.y = ground_altitude
	rot = hg.GetR(hg.Mat4LookAt(pos, target_pos))
	return pos, rot


def create_physic_ball(ball, pos, rot):
	_, mm = ball.GetObject().GetMinMax(Main.pipeline_res)
	size = (mm.mx - mm.mn)
	material = ball.GetObject().GetMaterial(0)
	new_node = hg.CreatePhysicSphere(Main.scene, size.x / 2, hg.TransformationMat4(pos, rot), Main.sphere_ref, [material], 1)
	new_node.GetRigidBody().SetType(hg.RBT_Dynamic)
	ball.GetTransform().SetParent(new_node)
	new_node.RemoveObject()
	rb = new_node.GetRigidBody()
	rb.SetRestitution(0.95)
	rb.SetLinearDamping(0.65)
	rb.SetAngularDamping(0.4)
	Main.scene_physics.NodeCreatePhysicsFromAssets(new_node)


def reset_balls():
	for i in range(len(Main.balls)):
		ball = Main.balls[i]
		bd = ball.GetTransform().GetParent()
		pos, rot = Main.balls_start_params[i][0], Main.balls_start_params[i][1]
		ball.GetTransform().ClearParent()
		Main.scene.DestroyNode(bd)
		create_physic_ball(ball, pos, rot)

	hg.SceneGarbageCollectSystems(Main.scene, Main.scene_physics)


def setup_collisions():
	Main.scene.Update(1000)
	Main.collision_nodes = []
	nodes = Main.scene.GetNode("pool_col_shape").GetInstanceSceneView().GetNodes(Main.scene)
	n = nodes.size()
	for i in range(n):
		nd = nodes.at(i)
		nm = nd.GetName()
		if "col_shape" in nm:
			_, mm = nd.GetObject().GetMinMax(Main.pipeline_res)
			size = (mm.mx - mm.mn)
			ref = Main.pipeline_res.AddModel('col_shape' + str(i), hg.CreateCubeModel(Main.vs_decl, size.x, size.y, size.z))
			pos = nd.GetTransform().GetPos()
			rot = nd.GetTransform().GetRot()
			parent = nd.GetTransform().GetParent()
			material = nd.GetObject().GetMaterial(0)
			new_node = hg.CreatePhysicCube(Main.scene, hg.Vec3(size), hg.TransformationMat4(hg.Vec3(pos), hg.Vec3(rot)), ref, [material], 0)
			new_node.SetName("ColBox_" + str(i))
			rb = new_node.GetRigidBody()
			if "table" in nm:
				rb.SetRestitution(0.15)
			else:
				rb.SetRestitution(0.8)
			Main.scene_physics.NodeCreatePhysicsFromAssets(new_node)
			new_node.GetTransform().SetParent(parent)
			new_node.RemoveObject()
			Main.scene.DestroyNode(nd)
			Main.collision_nodes.append(new_node)

	Main.scene_physics.SceneCreatePhysicsFromAssets(Main.scene)

	vtx_layout = hg.VertexLayoutPosFloatNormUInt8()
	ball_r = get_object_radius(Main.balls[0])
	sphere_mdl = hg.CreateSphereModel(vtx_layout, ball_r, 12, 24)
	Main.sphere_ref = Main.pipeline_res.AddModel('sphere', sphere_mdl)

	for ball in Main.balls:
		pos = ball.GetTransform().GetPos()
		rot = ball.GetTransform().GetRot()
		pos.y += 0.1
		Main.balls_start_params.append([pos, rot])
		ball.GetTransform().SetPos(hg.Vec3(0, 0, 0))
		ball.GetTransform().SetRot(hg.Vec3(0, 0, 0))
		create_physic_ball(ball, pos, rot)

	hg.SceneGarbageCollectSystems(Main.scene, Main.scene_physics)


def compute_stick_targeting_position():
	pos = Main.stick_targeting_params[0][0] * (1 - Main.shoot_level) + Main.stick_targeting_params[1][0] * Main.shoot_level
	rot = Main.stick_targeting_params[0][1] * (1 - Main.shoot_level) + Main.stick_targeting_params[1][1] * Main.shoot_level
	return pos, rot


# States

# Observation : You can turn around the table

def state_observation_update():
	if Animations.is_running():
		if not Animations.update_animations(Main.ts):
			camera = Main.scene.GetCurrentCamera()
			camera.GetTransform().SetPos(Main.anim_camera_pos.v)
			camera.GetTransform().SetRot(Main.anim_camera_rot.v)
			if Main.anim_stick_pos is not None:
				Main.stick.GetTransform().SetPos(Main.anim_stick_pos.v)
				Main.stick.GetTransform().SetRot(Main.anim_stick_rot.v)
		else:
			Animations.clear_animations()

	else:
		if Main.mouse.Pressed(hg.MB_1):
			reset_balls()

		elif Main.mouse.Down(hg.MB_0):
			if Main.current_ball_hover is None:
				camera = Main.scene.GetCurrentCamera()
				cam_pos = camera.GetTransform().GetPos()
				target_pos = Main.table_center.GetTransform().GetPos()
				cam_pos, cam_rot = compute_mouse_circular_pos(cam_pos, target_pos, Main.state_observation_camera_distance, Main.state_observation_camera_altitude)
				camera.GetTransform().SetPos(cam_pos)
				camera.GetTransform().SetRot(cam_rot)
			else:
				return setup_state_targeting()
		else:
			Main.current_ball_hover = hover_objects_test(Main.balls, Main.scene.GetCurrentCamera(), Main.resolution, hg.Vec2(Main.mouse.X(), Main.mouse.Y()))
			if Main.current_ball_hover is not None:
				ball_pos = hg.GetT(Main.current_ball_hover.GetTransform().GetWorld())
				p = get_screen_position(Main.scene.GetCurrentCamera(), ball_pos, Main.resolution)
				if p is not None:
					Main.selector.set_position(p.x, p.y + Main.selector_offset_y)
					Main.sprites_display_list.append(Main.selector)

	return state_observation_update


def setup_state_observation():
	camera = Main.scene.GetCurrentCamera()
	cam_pos_start = camera.GetTransform().GetPos()
	cam_rot_start = camera.GetTransform().GetRot()
	target = Main.scene.GetNode("table_center")
	target_pos = target.GetTransform().GetPos()
	cam_pos_dest, cam_rot_dest = compute_mouse_circular_pos(cam_pos_start, target_pos, Main.state_observation_camera_distance, Main.state_observation_camera_altitude)
	Animations.minimize_rotation_vec3(cam_rot_start, cam_rot_dest)
	Main.anim_camera_pos = Animation(Main.ts, 1, cam_pos_start, cam_pos_dest)
	Main.anim_camera_rot = Animation(Main.ts, 1, cam_rot_start, cam_rot_dest)

	if Main.flag_start:
		stick_mat_start = Main.stick.GetTransform().GetWorld()
		Main.stick.GetTransform().ClearParent()
		stick_pos_start = hg.GetT(stick_mat_start)
		stick_rot_start = hg.GetR(stick_mat_start)
		stick_pos_dest, stick_rot_dest = Main.stick_start_params[0], Main.stick_start_params[1]
		Main.stick.GetTransform().SetPos(stick_pos_start)
		Main.stick.GetTransform().SetRot(stick_rot_start)
		if cam_pos_dest.z < 0.74:
			stick_rot_start.x -= 2 * pi
		Main.anim_stick_pos = Animation(Main.ts, 1, stick_pos_start, stick_pos_dest)
		Main.anim_stick_rot = Animation(Main.ts, 1, stick_rot_start, stick_rot_dest)

	return state_observation_update


# Targeting: Spin around the ball and determine the strength of the cue.

def state_targeting_update():
	if Animations.is_running():
		if not Animations.update_animations(Main.ts):
			camera = Main.scene.GetCurrentCamera()
			camera.GetTransform().SetPos(Main.anim_camera_pos.v)
			camera.GetTransform().SetRot(Main.anim_camera_rot.v)
			Main.stick.GetTransform().SetPos(Main.anim_stick_pos.v)
			Main.stick.GetTransform().SetRot(Main.anim_stick_rot.v)
		else:
			Animations.clear_animations()
	else:
		if Main.mouse.Pressed(hg.MB_0):
			shoot_v = hg.GetZ(Main.scene.GetCurrentCamera().GetTransform().GetWorld())
			shoot_v.y = 0
			shoot_v = hg.Normalize(shoot_v)
			Main.shoot_ball = Main.current_ball_hover
			imp = Main.impulse_range[0] * (1 - Main.shoot_level) + Main.impulse_range[1] * Main.shoot_level
			Main.shoot_v = shoot_v * imp
			Main.shoot_p = hg.GetT(Main.shoot_ball.GetTransform().GetWorld())
			return setup_state_shoot()

		elif Main.mouse.Pressed(hg.MB_1):
			return setup_state_observation()

		else:
			camera = Main.scene.GetCurrentCamera()
			cam_pos = camera.GetTransform().GetPos()
			target = Main.current_ball_hover
			target_pos = hg.GetT(target.GetTransform().GetWorld())
			cam_pos, cam_rot = compute_mouse_circular_pos(cam_pos, target_pos, Main.state_targeting_camera_distance, Main.state_targeting_camera_altitude)
			camera.GetTransform().SetPos(cam_pos)
			camera.GetTransform().SetRot(cam_rot)
			mw = Main.mouse.Wheel()
			Main.shoot_level = max(0, min(1, Main.shoot_level + mw * 0.05))
			Main.state_targeting_camera_distance = (Main.state_targeting_distance_range[0] * (1 - Main.shoot_level)) + Main.state_targeting_distance_range[1] * Main.shoot_level
			Main.state_targeting_camera_altitude = (Main.state_targeting_altitude_range[0] * (1 - Main.shoot_level)) + Main.state_targeting_altitude_range[1] * Main.shoot_level
			Main.state_targeting_camera_altitude += target_pos.y
			pos, rot = compute_stick_targeting_position()
			Main.stick.GetTransform().SetPos(pos)
			Main.stick.GetTransform().SetRot(rot)

	return state_targeting_update


def setup_state_targeting():
	camera = Main.scene.GetCurrentCamera()
	cam_pos_start = camera.GetTransform().GetPos()
	cam_rot_start = camera.GetTransform().GetRot()
	target = Main.current_ball_hover
	target_pos = hg.GetT(target.GetTransform().GetWorld())
	cam_pos_dest, cam_rot_dest = compute_mouse_circular_pos(cam_pos_start, target_pos, Main.state_targeting_camera_distance, Main.state_targeting_camera_altitude)
	Animations.minimize_rotation_vec3(cam_rot_start, cam_rot_dest)
	Main.anim_camera_pos = Animation(Main.ts, 1, cam_pos_start, cam_pos_dest)
	Main.anim_camera_rot = Animation(Main.ts, 1, cam_rot_start, cam_rot_dest)
	Main.stick.GetTransform().SetParent(Main.scene.GetCurrentCamera())
	stick_mat_start = Main.stick.GetTransform().GetWorld()
	stick_pos_dest, stick_rot_dest = compute_stick_targeting_position()
	cam_mat = hg.InverseFast(Main.scene.GetCurrentCamera().GetTransform().GetWorld())
	stick_mat_start = cam_mat * stick_mat_start
	stick_pos_start = hg.GetT(stick_mat_start)
	stick_rot_start = hg.GetR(stick_mat_start)
	Main.stick.GetTransform().SetPos(stick_pos_start)
	Main.stick.GetTransform().SetRot(stick_rot_start)
	if cam_pos_start.z < 0.74:
		stick_rot_dest.x -= 2 * pi
	Main.anim_stick_pos = Animation(Main.ts, 1, stick_pos_start, stick_pos_dest)
	Main.anim_stick_rot = Animation(Main.ts, 1, stick_rot_start, stick_rot_dest)
	return state_targeting_update


# Shoot - Animation: The cue shoot the ball

def setup_state_shoot():
	stick_mat_start = Main.stick.GetTransform().GetWorld()
	Main.stick.GetTransform().ClearParent()
	stick_pos_start = hg.GetT(stick_mat_start)
	stick_rot_start = hg.GetR(stick_mat_start)
	Main.stick.GetTransform().SetPos(stick_pos_start)
	Main.stick.GetTransform().SetRot(stick_rot_start)
	v = Main.shoot_p - stick_pos_start
	distance = hg.Len(v) - get_object_radius(Main.shoot_ball)
	stick_pos_dest = stick_pos_start + hg.Normalize(v) * distance
	stick_rot_dest = hg.Vec3(0, stick_rot_start.y, -10 / 180 * pi)
	Main.anim_stick_pos = Animation(Main.ts, 0.25, stick_pos_start, stick_pos_dest, Animations.TWEEN_EASEINQUAD)
	Main.anim_stick_rot = Animation(Main.ts, 0.25, stick_rot_start, stick_rot_dest)
	return state_shoot_update


def state_shoot_update():
	if Animations.is_running():
		if not Animations.update_animations(Main.ts):
			Main.stick.GetTransform().SetPos(Main.anim_stick_pos.v)
			Main.stick.GetTransform().SetRot(Main.anim_stick_rot.v)
		else:
			ball_rb = Main.shoot_ball.GetTransform().GetParent()
			Animations.clear_animations()
			Main.scene_physics.NodeWake(ball_rb)
			Main.scene_physics.NodeAddImpulse(ball_rb, Main.shoot_v, Main.shoot_p)
	else:
		Main.stick.GetTransform().SetParent(Main.scene.GetCurrentCamera())
		stick_mat_start = Main.stick.GetTransform().GetWorld()
		cam_mat = hg.InverseFast(Main.scene.GetCurrentCamera().GetTransform().GetWorld())
		stick_mat_start = cam_mat * stick_mat_start
		stick_pos_start = hg.GetT(stick_mat_start)
		stick_rot_start = hg.GetR(stick_mat_start)
		Main.stick.GetTransform().SetPos(stick_pos_start)
		Main.stick.GetTransform().SetRot(stick_rot_start)
		return setup_state_idle()

	return state_shoot_update


# Idle: Wait until the balls stops. You can turn around the table.

def state_idle_update():
	if Animations.is_running():
		if not Animations.update_animations(Main.ts):
			camera = Main.scene.GetCurrentCamera()
			camera.GetTransform().SetPos(Main.anim_camera_pos.v)
			camera.GetTransform().SetRot(Main.anim_camera_rot.v)
			Main.stick.GetTransform().SetPos(Main.anim_stick_pos.v)
			Main.stick.GetTransform().SetRot(Main.anim_stick_rot.v)
		else:
			Animations.clear_animations()

	else:
		flag_hold = True
		for ball in Main.balls:
			vel = hg.Len(Main.scene_physics.NodeGetLinearVelocity(ball.GetTransform().GetParent()))
			if vel > 1e-2:
				flag_hold = False
				break

		for ball in Main.balls:
			y = hg.GetT(ball.GetTransform().GetParent().GetTransform().GetWorld()).y
			if y < Main.table_center.GetTransform().GetPos().y:
				reset_balls()
				break

		if flag_hold:
			return setup_state_observation()

		if Main.mouse.Pressed(hg.MB_1):
			reset_balls()

		if Main.mouse.Down(hg.MB_0):
			camera = Main.scene.GetCurrentCamera()
			cam_pos = camera.GetTransform().GetPos()
			target = Main.scene.GetNode("table_center")
			target_pos = target.GetTransform().GetPos()
			cam_pos, cam_rot = compute_mouse_circular_pos(cam_pos, target_pos, Main.state_observation_camera_distance, Main.state_observation_camera_altitude)
			camera.GetTransform().SetPos(cam_pos)
			camera.GetTransform().SetRot(cam_rot)

	return state_idle_update


def setup_state_idle():
	camera = Main.scene.GetCurrentCamera()
	cam_pos_start = camera.GetTransform().GetPos()
	cam_rot_start = camera.GetTransform().GetRot()
	target = Main.scene.GetNode("table_center")
	target_pos = target.GetTransform().GetPos()
	cam_pos_dest, cam_rot_dest = compute_mouse_circular_pos(cam_pos_start, target_pos, Main.state_observation_camera_distance, Main.state_observation_camera_altitude)
	Animations.minimize_rotation_vec3(cam_rot_start, cam_rot_dest)
	Main.anim_camera_pos = Animation(Main.ts, 0.5, cam_pos_start, cam_pos_dest)
	Main.anim_camera_rot = Animation(Main.ts, 0.5, cam_rot_start, cam_rot_dest)

	stick_pos_start = Main.stick.GetTransform().GetPos()
	stick_rot_start = Main.stick.GetTransform().GetRot()
	stick_pos_dest, stick_rot_dest = Main.stick_idle_params[0], Main.stick_idle_params[1]
	Main.anim_stick_pos = Animation(Main.ts, 1, stick_pos_start, stick_pos_dest)
	Main.anim_stick_rot = Animation(Main.ts, 1, stick_rot_start, stick_rot_dest)

	return state_idle_update


# Init renderer

init_game()

# Init state:

Main.current_state = setup_state_observation()
Main.flag_start = True

# Main loop

Main.frame = 0
hg.ResetClock()

while not Main.keyboard.Pressed(hg.K_Escape):

	f, res_x, res_y = hg.RenderResetToWindow(Main.win, res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X | hg.RF_MaxAnisotropy)
	if f:
		Main.resolution.x, Main.resolution.y = res_x, res_y

	Main.mouse.Update()
	Main.keyboard.Update()

	dt = hg.TickClock()

	if dt > 1:
		Main.ts += hg.time_to_sec_f(dt)

		# Update scene
		hg.SceneUpdateSystems(Main.scene, Main.clocks, dt, Main.scene_physics, Main.physic_step, 10)

		#  Update current state
		Main.current_state = Main.current_state()

		# Display scene
		view_state = Main.scene.ComputeCurrentCameraViewState(hg.ComputeAspectRatioX(res_x, res_y))
		if Main.flag_AAA:
			vid, passId = hg.SubmitSceneToPipeline(0, Main.scene, hg.IntRect(0, 0, res_x, res_y), True, Main.pipeline, Main.pipeline_res, Main.pipeline_aaa, Main.pipeline_aaa_config, Main.frame)
		else:
			vid, passId = hg.SubmitSceneToPipeline(0, Main.scene, hg.IntRect(0, 0, res_x, res_y), view_state, Main.pipeline, Main.pipeline_res)

		# Display overlays

		hg.SetViewRect(vid, 0, 0, res_x, res_y)
		hg.SetViewClear(vid, hg.CF_Depth, 0, 1.0, 0)
		Sprite.setup_matrix_sprites2D(vid, Main.resolution)

		for spr in Main.sprites_display_list:
			spr.draw(vid)
		vid += 1

	# Display physics debug:

	# display_physics_debug(vid)

	Main.sprites_display_list = []

	Main.frame = hg.Frame()

	hg.UpdateWindow(Main.win)

hg.RenderShutdown()
hg.DestroyWindow(Main.win)
