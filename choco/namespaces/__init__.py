import os
import jams

ns_dir = os.path.dirname(os.path.abspath(__file__))

# New chord namespaces
jams.schema.add_namespace(os.path.join(ns_dir, "chord_ireal.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_jparser_harte.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_jparser_functional.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_m21_leadsheet.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_m21_abc.json"))
jams.schema.add_namespace(os.path.join(ns_dir, "chord_weimar.json"))

# New symbolic namespaces
jams.schema.add_namespace(os.path.join(ns_dir, "timesig.json"))
