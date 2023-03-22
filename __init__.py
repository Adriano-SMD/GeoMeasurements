# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>


bl_info = {
    "name": "GeoMeasurements",
    "author": "Adriano A. Oliveira, ChatGPT 4",
    "version": (0, 2),
    "blender": (2, 93, 0),
    "location": "View3D > Sidebar > GeoMeasurements",
    "description": "Medições geomorfológicas",
    "category": "Measurements",
}

import bpy
import math
import os

# Define caminho do add-on e arquivo com coleções e objetos a serem importados
addon_directory = os.path.dirname(os.path.abspath(__file__))
blend_file_path = os.path.join(addon_directory, "Measurements.blend")

# Parâmetros para segemntos de reta
BEVEL_DEPTH = 0.05
SEGMENT_COLOR = [1, 1, 0, 1]

# Adiciona uma coleção de objetos e suas dependências à cena
def append_measurements_collection(collection_name):
    if bpy.data.collections.get(collection_name) is None:
        with bpy.data.libraries.load(blend_file_path) as (data_from, data_to):
            data_to.collections = [collection_name]

        for collection in data_to.collections:
            bpy.context.scene.collection.children.link(collection)

# Cria objetos Observer e Observed, se eles não existirem
def create_observer_and_observed():
    append_measurements_collection("Measurements") 

    gizmo_observer = bpy.data.collections.get("Gizmo_Observer")
    gizmo_observed = bpy.data.collections.get("Gizmo_Observed")

    measurements_collection = bpy.data.collections.get("Measurements")
    if not measurements_collection:
        measurements_collection = bpy.data.collections.new("Measurements")
        bpy.context.scene.collection.children.link(measurements_collection)

    observer = bpy.data.objects.get("Observer")
    if observer is None:
        observer_instance = bpy.data.objects.new("Observer", None)
        observer_instance.instance_type = 'COLLECTION'
        observer_instance.instance_collection = gizmo_observer
        measurements_collection.objects.link(observer_instance)

    observed = bpy.data.objects.get("Observed")
    if observed is None:
        observed_instance = bpy.data.objects.new("Observed", None)
        observed_instance.instance_type = 'COLLECTION'
        observed_instance.instance_collection = gizmo_observed
        measurements_collection.objects.link(observed_instance)

    observer = bpy.data.objects.get("Observer")
    observed = bpy.data.objects.get("Observed")

    return observer, observed

# Obtém objetos Observer e Observed
def get_observer_and_observed():
    observer = bpy.data.objects.get("Observer")
    observed = bpy.data.objects.get("Observed")
    return observer, observed

# Calcula as medições com base nas posições dos objetos observador e observado
def calculate_measurements(observer, observed):
    if not observer or not observed:
        return None

    vector = observed.location - observer.location
    distance = vector.length
    azimuth = math.degrees(math.atan2(vector.x, vector.y)) % 360
    dip = math.degrees(math.atan2(vector.z, math.sqrt(vector.x**2 + vector.y**2)))
    alt_observer = observer.location.z
    alt_observed = observed.location.z

    return {
        "distance": distance,
        "azimuth": azimuth,
        "dip": dip,
        "alt_observer": alt_observer,
        "alt_observed": alt_observed,
    }

# Obtém ou criea uma coleção com base em 'collection_name'
def get_or_create_collection(collection_name):
    collection = bpy.data.collections.get(collection_name)
    if not collection:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    return collection

# Cria um objeto de texto com parâmetros especificados
def create_text_object(name, text, align_y, location, parent=None):
    # Create a new text object with a given name, text content, and location
    text_data = bpy.data.curves.new(name, type='FONT')
    text_data.body = text
    
    # Centraliza o alinhamento vertical do texto
    text_data.align_y = align_y

    text_object = bpy.data.objects.new(name, text_data)
    text_object.location = location
    # Set the text object's parent if specified
    if parent:
        text_object.parent = parent

    return text_object

# Cria um segmento de reta entre os pontos e um texto 3D que exibe as medidas
def create_measurement():
    observer, observed = get_observer_and_observed()
    if not observer or not observed:
        return

    measurements_collection = get_or_create_collection("Measurements")

    segment = create_segment_object(observer, observed)
    measurements_collection.objects.link(segment)

    measurements = calculate_measurements(observer, observed)
    measurement_text = (
        f"Alt 1: {measurements['alt_observer']:.1f}m\n"
        f"Alt 2: {measurements['alt_observed']:.1f}m\n"
        f"Distância: {measurements['distance']:.1f}m\n"
        f"Azimute: {measurements['azimuth']:.3f}°\n"
        f"Mergulho: {measurements['dip']:.3f}°"
    )

    # Calcular vetor entre observador e observado
    vector = observed.location - observer.location
    vector.normalize()

    # Calcular ângulos de rotação com base no vetor
    rotation_x = math.atan2(vector.z, math.sqrt(vector.x**2 + vector.y**2))
    rotation_z = math.atan2(vector.y, vector.x)

    # Criar objeto de texto com a rotação correta
    text_object = create_text_object("Measurements", measurement_text, "CENTER", (observer.location + observed.location) / 2, parent=segment)
    text_object.rotation_euler[0] = rotation_x
    text_object.rotation_euler[2] = rotation_z - math.pi / 2

    text_object.color = SEGMENT_COLOR

    material = bpy.data.materials.get("Geo_04")
    if material:
        text_object.data.materials.append(material)

    measurements_collection.objects.link(text_object)


# Cria um segmento de reta
def create_segment_object(observer, observed):
    curve_data = bpy.data.curves.new("Segment", type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.resolution_u = 1
    curve_data.bevel_mode = 'ROUND'
    curve_data.bevel_depth = BEVEL_DEPTH

    spline = curve_data.splines.new('BEZIER')
    spline.bezier_points.add(1)
    spline.bezier_points[0].co = observer.location
    spline.bezier_points[1].co = observed.location

    segment = bpy.data.objects.new("Segment", curve_data)
    segment.hide_select = True
    segment.color = SEGMENT_COLOR

    material = bpy.data.materials.get("Geo_04")
    if material:
        segment.data.materials.append(material)

    return segment

# Define painel principal do add-on
class MeasurementPanel(bpy.types.Panel):
    bl_label = "GeoMeasurements"
    bl_idname = "OBJECT_PT_measurement"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'GeoMeasurements'

    def draw(self, context):
        layout = self.layout
        observer, observed = get_observer_and_observed()

        if observer and observed:
            measurements = calculate_measurements(observer, observed)
            distance, azimuth, dip, alt_observer, alt_observed = measurements.values()
            layout.label(text=f"Alt 1: {alt_observer:.1f}m")
            layout.label(text=f"Alt 2: {alt_observed:.1f}m")
            layout.label(text=f"Distância: {distance:.1f}m")
            layout.label(text=f"Azimute: {azimuth:.3f}°")
            layout.label(text=f"Mergulho: {dip:.3f}°")
            layout.separator()
            layout.operator("measurement.fix_measurement", text="Fixar")
        else:
            layout.label(text="Crie os objetos de medição")
            layout.operator("measurement.create_observer_and_observed", text="Criar")

# Botão CRIAR
class CreateObserverAndObservedOperator(bpy.types.Operator):
    bl_idname = "measurement.create_observer_and_observed"
    bl_label = "Create Observer and Observed"
    bl_description = "Cria objetos de medição"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        create_observer_and_observed()
        return {'FINISHED'}

# Botão FIXAR
class FixMeasurementOperator(bpy.types.Operator):
    bl_idname = "measurement.fix_measurement"
    bl_label = "Fix Measurement"
    bl_description = "Cria segmento com medições entre pontos "
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        create_measurement()
        return {'FINISHED'}

# Adiciona os operadores e painéis ao Blender
def register():
    bpy.utils.register_class(MeasurementPanel)
    bpy.utils.register_class(FixMeasurementOperator)
    bpy.utils.register_class(CreateObserverAndObservedOperator)

# Remove os operadores e painéis do Blender
def unregister():
    bpy.utils.unregister_class(MeasurementPanel)
    bpy.utils.unregister_class(FixMeasurementOperator)
    bpy.utils.unregister_class(CreateObserverAndObservedOperator)

if __name__ == "__main__":
    register()