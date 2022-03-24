# Animations

import harfang as hg
from math import cos, pi


class Animations:
	animations = []

	TWEEN_COS = 0
	TWEEN_EASEINQUAD = 1

	@staticmethod
	def interpolation_lineaire(a, b, t):
		return a * (1 - t) + b * t

	@staticmethod
	def interpolation_cosinusoidale(a, b, t):
		return Animations.interpolation_lineaire(a, b, (-cos(pi * t) + 1) / 2)

	@staticmethod
	def easeInQuad(t, b, c, d):
		t /= d
		return c * t * t + b

	@staticmethod
	def minimize_angle_delta(angle_strt, angle_dest):
		delta = angle_dest - angle_strt
		if abs(delta) > pi:
			delta_min = 2*pi - abs(delta)
			if angle_strt > angle_dest:
				return angle_strt + delta_min
			else:
				return angle_strt - delta_min
		return angle_dest

	@classmethod
	def minimize_rotation_vec3(cls, rot_start, rot_dest):
		rot_dest.x = cls.minimize_angle_delta(rot_start.x, rot_dest.x)
		rot_dest.y = cls.minimize_angle_delta(rot_start.y, rot_dest.y)
		rot_dest.z = cls.minimize_angle_delta(rot_start.z, rot_dest.z)

	@classmethod
	def update_animations(cls, t):
		flag_end = True
		for anim in cls.animations:
			flag_end &= anim.update(t)
		return flag_end

	@classmethod
	def clear_animations(cls):
		cls.animations = []

	@classmethod
	def is_running(cls):
		if len(cls.animations) == 0:
			return False
		return True


class Animation:

	def __init__(self, t_start, delay, v_start, v_end, tween_type=Animations.TWEEN_COS):
		self.t_start = t_start
		self.delay = delay
		self.v_start = v_start
		self.v_end = v_end
		self.v = v_start
		self.tween_type = tween_type
		self.flag_end = False
		Animations.animations.append(self)

	def update(self, t):
		if t > self.t_start + self.delay:
			self.v = self.v_end
			self.flag_end = True
		elif t >= self.t_start:
			if self.tween_type == Animations.TWEEN_COS:
				self.v = Animations.interpolation_cosinusoidale(self.v_start, self.v_end, (t - self.t_start) / self.delay)
			elif self.tween_type == Animations.TWEEN_EASEINQUAD:
				self.v = Animations.easeInQuad((t - self.t_start), self.v_start, self.v_end-self.v_start, self.delay)
		else:
			self.v = self.v_start
		return self.flag_end
