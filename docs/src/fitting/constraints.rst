======================
Constraints
======================

Constraints can be applied to :class:`easyCore.Objects.Base.Parameter` directly or to the :class:`easyCore.Fitting.Fitting.Fitter` class. Constraints are evaluated at creation and on value change.

Anatomy of a constraint
-----------------------

A constraint is a rule which is applied to a **dependent** variable. This rule can consist of a logical operation or a relation to one or more **independent** variables.


Constraints on Parameters
^^^^^^^^^^^^^^^^^^^^^^^^^

:class:`easyCore.Objects.Base.Parameter` has the properties `builtin_constraints` and `user_constraints`. These are dictionaries which correspond to constraints which are intrinsic and extrinsic to the Parameter. This means that on the value change of the Parameter firstly the `builtin_constraints` are evaluated, followed by the `user_constraints`.


Constraints on Fitting
^^^^^^^^^^^^^^^^^^^^^^

:class:`easyCore.Fitting.Fitting.Fitter` has the ability to evaluate user supplied constraints which effect the

Constraint Reference
--------------------

.. minigallery:: easyCore.Fitting.Constraints.NumericConstraint
    :add-heading: Examples using `Constraints`

Built-in constraints
^^^^^^^^^^^^^^^^^^^^

These are the built in constraints which you can use

.. autoclass:: easyCore.Fitting.Constraints.SelfConstraint
   :members:
   :inherited-members:

.. autoclass:: easyCore.Fitting.Constraints.NumericConstraint
  :members:

.. autoclass:: easyCore.Fitting.Constraints.ObjConstraint
  :members:

.. autoclass:: easyCore.Fitting.Constraints.FunctionalConstraint
  :members:

.. autoclass:: easyCore.Fitting.Constraints.MultiObjConstraint
  :members:

User created constraints
^^^^^^^^^^^^^^^^^^^^^^^^

You can make your own constraints

.. autoclass:: easyCore.Fitting.Constraints.ConstraintBase
  :members: