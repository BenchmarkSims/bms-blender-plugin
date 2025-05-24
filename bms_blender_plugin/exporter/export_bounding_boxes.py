import operator
import os

def export_bounding_boxes(bounding_boxes, file_directory):
    """
    Exports bounding box data as required for <aircraft>>.txtpb file.
    Output will still need to be written to <aircraft>>.txtpb by users, but this at least gets them the
    information in the correct format.
    """
    bounding_boxes_filepath = os.path.join(file_directory, "bounding_boxes.txtpb")

    with open(bounding_boxes_filepath, "w") as bounding_box_file:
        bounding_box_file.write("# The following data needs to be manually added to the required <aircraft>.txtpb file\n")

        for bounding_box in bounding_boxes:
            bounding_box_file.write(bounding_box.bbox_to_txtpb_format())
            
    print(f"bounding_boxes.txtpb: {bounding_boxes_filepath}")
