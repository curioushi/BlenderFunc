blenderfunc.object
==========================================

.. currentmodule:: blenderfunc

Camera
------------------------
.. autofunction:: set_camera

LightSource
------------------------
.. autofunction:: set_projector
.. autofunction:: set_background_light
.. autofunction:: add_light

Mesh
------------------------
.. autofunction:: add_object_from_file
.. autofunction:: add_plane
.. autofunction:: add_cube
.. autofunction:: add_cylinder
.. autofunction:: add_ball
.. autofunction:: add_tote
.. autofunction:: decimate_mesh_object
.. autofunction:: remove_mesh_object
.. autofunction:: remove_highest_mesh_object
.. autofunction:: duplicate_mesh_object
.. autofunction:: separate_isolated_meshes
.. autofunction:: export_mesh_object
.. autofunction:: export_meshes_info
.. autofunction:: get_all_mesh_objects
.. autofunction:: get_mesh_objects_by_custom_properties
.. autofunction:: set_origin_to_center_of_mass

Texture
------------------------
.. autofunction:: load_image
.. autofunction:: get_pbr_material_infos
.. autofunction:: add_pbr_material
.. autofunction:: add_simple_material
.. autofunction:: set_material
.. autofunction:: get_hdr_material_infos
.. autofunction:: set_hdr_background
.. autofunction:: add_transparent_material

Physics
------------------------
.. autofunction:: physics_simulation
.. autofunction:: collision_free_positioning

PoseSampler
------------------------
.. autofunction:: in_tote_sampler
.. autofunction:: in_view_checker
.. autofunction:: in_views_sampler
