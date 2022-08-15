import os
import jams

ns_dir = os.path.dirname(os.path.abspath(__file__))

jams.schema.add_namespace(os.path.join(ns_dir, "./chord_har.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_ireal.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_jparser_harte.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_jparser_functional.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_m21.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_weimar.json"))
