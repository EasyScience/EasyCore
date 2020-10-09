__author__ = 'github.com/wardsimon'
__version__ = '0.0.1'

CIF_DICT = {
    'easyCore.Elements.Basic.SpaceGroup.SpaceGroup':                 [
        {
            'internal':   '_space_group_HM_name',
            'external':   {
                'required': ['symmetry_space_group_name_H-M', 'space_group_name_H-M_alt'],
            },
            'output':     'symmetry_space_group_name_H-M',
            'additional': []
        }
    ],
    'easyCore.Elements.Basic.Site.Site':                             [
        {
            'internal':   'label',
            'external':   {
                'required': ['atom_site_label'],
            },
            'output':     'atom_site_label',
            'additional': []
        },
        {
            'internal':   'specie',
            'external':   {
                'required': ['atom_site_type_symbol'],
            },
            'output':     'atom_site_type_symbol',
            'additional': []
        },
        {
            'internal':   'occupancy',
            'external':   {
                'required': ['atom_site_occupancy'],
            },
            'output':     'atom_site_occupancy',
            'additional': []
        },
        {
            'internal':   'fract_x',
            'external':   {
                'required': ['atom_site_fract_x'],
            },
            'output':     'atom_site_fract_x',
            'additional': []
        },
        {
            'internal': 'fract_y',
            'external': {
                'required': ['atom_site_fract_y'],
            },
            'output':   'atom_site_fract_y',
        },
        {
            'internal':   'fract_z',
            'external':   {
                'required': ['atom_site_fract_z'],
            },
            'output':     'atom_site_fract_z',
            'additional': []
        }
    ],
    'easyCore.Elements.Basic.Cell.Cell':                             [
        {
            'internal':   'length_a',
            'external':   {
                'required': ['cell_length_a'],
            },
            'output':     'cell_length_a',
            'additional': []
        },
        {
            'internal':   'length_b',
            'external':   {
                'required': ['cell_length_b'],
            },
            'output':     'cell_length_b',
            'additional': []
        },
        {
            'internal':   'length_c',
            'external':   {
                'required': ['cell_length_c'],
            },
            'output':     'cell_length_c',
            'additional': []
        },
        {
            'internal':   'angle_alpha',
            'external':   {
                'required': ['cell_angle_alpha'],
            },
            'output':     'cell_angle_alpha',
            'additional': []
        },
        {
            'internal':   'angle_beta',
            'external':   {
                'required': ['cell_angle_beta'],
            },
            'output':     'cell_angle_beta',
            'additional': []
        },
        {
            'internal':   'angle_gamma',
            'external':   {
                'required': ['cell_angle_gamma'],
            },
            'output':     'cell_angle_gamma',
            'additional': []
        },
    ],
    'easyCore.Elements.Basic.AtomicDisplacement.AtomicDisplacement': [
        {
            'internal':   'adp_class',
            'external':   {
                'required': ['atom_site_adp_type'],
            },
            'output':     'atom_site_adp_type',
            'additional': [['atom_site_label', 'atom_site_aniso_label']]
        },
    ],
    'easyCore.Elements.Basic.AtomicDisplacement.IsotropicU':         [
        {
            'internal':   'Uiso',
            'external':   {
                'required': ['atom_site_U_iso_or_equiv'],
            },
            'output':     'atom_site_U_iso_or_equiv',
            'additional': []
        },
    ],
    'easyCore.Elements.Basic.AtomicDisplacement.Anisotropic':        [
        {
            'internal':   'U_11',
            'external':   {
                'required': ['atom_site_aniso_U_11'],
            },
            'output':     'atom_site_aniso_U_11',
            'additional': []
        },
        {
            'internal':   'U_12',
            'external':   {
                'required': ['atom_site_aniso_U_12'],
            },
            'output':     'atom_site_aniso_U_12',
            'additional': []
        },
        {
            'internal':   'U_13',
            'external':   {
                'required': ['atom_site_aniso_U_13'],
            },
            'output':     'atom_site_aniso_U_13',
            'additional': []
        },
        {
            'internal':   'U_22',
            'external':   {
                'required': ['atom_site_aniso_U_22'],
            },
            'output':     'atom_site_aniso_U_22',
            'additional': []
        },
        {
            'internal':   'U_23',
            'external':   {
                'required': ['atom_site_aniso_U_23'],
            },
            'output':     'atom_site_aniso_U_23',
            'additional': []
        },
        {
            'internal':   'U_33',
            'external':   {
                'required': ['atom_site_aniso_U_33'],
            },
            'output':     'atom_site_aniso_U_33',
            'additional': []
        },
    ],
    'easyCore.Elements.Basic.AtomicDisplacement.IsotropicB':         [
        {
            'internal':   'Biso',
            'external':   {
                'required': ['atom_site_B_iso_or_equiv'],
            },
            'output':     'atom_site_B_iso_or_equiv',
            'additional': []
        },
    ],
    'easyCore.Elements.Basic.AtomicDisplacement.AnisotropicBij':     [
        {
            'internal':   'B_11',
            'external':   {
                'required': ['atom_site_aniso_B_11'],
            },
            'output':     'atom_site_aniso_B_11',
            'additional': []
        },
        {
            'internal':   'B_12',
            'external':   {
                'required': ['atom_site_aniso_B_12'],
            },
            'output':     'atom_site_aniso_B_12',
            'additional': []
        },
        {
            'internal':   'B_13',
            'external':   {
                'required': ['atom_site_aniso_B_13'],
            },
            'output':     'atom_site_aniso_B_13',
            'additional': []

        },
        {
            'internal':   'B_22',
            'external':   {
                'required': ['atom_site_aniso_B_22'],
            },
            'output':     'atom_site_aniso_B_22',
            'additional': []
        },
        {
            'internal':   'B_23',
            'external':   {
                'required': ['atom_site_aniso_B_23'],
            },
            'output':     'atom_site_aniso_B_23',
            'additional': []
        },
        {
            'internal':   'B_33',
            'external':   {
                'required': ['atom_site_aniso_B_33'],
            },
            'output':     'atom_site_aniso_B_33',
            'additional': []
        },
    ]
}

ADP_DICT = {
    'iso': {
        'Uiso': CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.IsotropicU'][0]['output'],
        'Biso': CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.IsotropicB'][0]['output'],
    },
    'ani': {
        'Uani': [U['output'] for U in CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.Anisotropic']],
        'Bani': [U['output'] for U in CIF_DICT['easyCore.Elements.Basic.AtomicDisplacement.AnisotropicBij']]
    }
}