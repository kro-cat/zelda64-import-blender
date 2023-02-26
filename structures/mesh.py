class Mesh:
    def __init__(self):
        self.verts, self.uvs, self.colors, self.faces = [], [], [], []
        self.faces_use_smooth = []
        self.vgroups = {}
        # import normals
        self.normals = []

    def create(self, name_format, hierarchy, offset, use_normals, prefix=""):
        log = getLogger('Mesh.create')
        if len(self.faces) == 0:
            log.trace('Skipping empty mesh %08X', offset)
            if self.verts:
                log.warning('Discarding unused vertices, no faces')
            return
        log.trace('Creating mesh %08X', offset)

        me_name = prefix + (name_format % ('me_%08X' % offset))
        me = bpy.data.meshes.new(me_name)
        ob = bpy.data.objects.new(prefix + (name_format % ('ob_%08X' % offset)), me)
        bpy.context.scene.objects.link(ob)
        bpy.context.scene.objects.active = ob
        me.vertices.add(len(self.verts))

        for i in range(len(self.verts)):
            me.vertices[i].co = self.verts[i]
        me.tessfaces.add(len(self.faces))
        vcd = me.tessface_vertex_colors.new().data
        for i in range(len(self.faces)):
            me.tessfaces[i].vertices = self.faces[i]
            me.tessfaces[i].use_smooth = self.faces_use_smooth[i]

            vcd[i].color1 = self.colors[i * 3]
            vcd[i].color2 = self.colors[i * 3 + 1]
            vcd[i].color3 = self.colors[i * 3 + 2]
        uvd = me.tessface_uv_textures.new().data
        for i in range(len(self.faces)):
            material = self.uvs[i * 4]
            if material:
                if not material.name in me.materials:
                    me.materials.append(material)
                uvd[i].image = material.texture_slots[0].texture.image
            uvd[i].uv[0] = self.uvs[i * 4 + 1]
            uvd[i].uv[1] = self.uvs[i * 4 + 2]
            uvd[i].uv[2] = self.uvs[i * 4 + 3]
        me.calc_normals()
        me.validate()
        me.update()

        log.debug('me =\n%r', me)
        log.debug('verts =\n%r', self.verts)
        log.debug('faces =\n%r', self.faces)
        log.debug('normals =\n%r', self.normals)

        if use_normals:
            # fixme make sure normals are set in the right order
            # fixme duplicate faces make normal count not the loop count
            loop_normals = []
            for face_normals in self.normals:
                loop_normals.extend(n for vi,n in face_normals)
            me.use_auto_smooth = True
            try:
                me.normals_split_custom_set(loop_normals)
            except:
                log.exception('normals_split_custom_set failed, known issue due to duplicate faces')

        if hierarchy:
            for name, vgroup in self.vgroups.items():
                grp = ob.vertex_groups.new(name)
                for v in vgroup:
                    grp.add([v], 1.0, 'REPLACE')
            ob.parent = hierarchy.armature
            mod = ob.modifiers.new(hierarchy.name, 'ARMATURE')
            mod.object = hierarchy.armature
            mod.use_bone_envelopes = False
            mod.use_vertex_groups = True
            mod.show_in_editmode = True
            mod.show_on_cage = True
