import sys
from niveristand import decorators, RealTimeSequence
from niveristand.clientapi.datatypes import DoubleValue, I32Value
from niveristand.exceptions import TranslateError, VeristandError
from niveristand.library.tasks import multitask, nivs_yield, stop_task, task
import pytest
from testutilities import rtseqrunner, validation


def _invalid():
    pass


@decorators.NivsParam('param', DoubleValue(0), False)
@decorators.nivs_rt_sequence
def return_param_plus_1(param):
    a = DoubleValue(0)
    a.value = param.value + 1
    return a.value


@decorators.nivs_rt_sequence
def stop_task_simple():
    a = I32Value(1)
    with multitask() as mt:
        @task(mt)
        def f1():
            pass

        @task(mt)
        def f2():
            stop_task(f1)
    return a.value


@decorators.nivs_rt_sequence
def stop_task_invalid_task_name():
    a = I32Value(1)
    with multitask() as mt:
        @task(mt)
        def f1():
            pass

        @task(mt)
        def f2():
            stop_task(_invalid)
    return a.value


@decorators.nivs_rt_sequence
def stop_task_invalid_task_name1():
    a = I32Value(1)
    with multitask() as mt:
        @task(mt)
        def f1():
            pass

        @task(mt)
        def f2():
            stop_task("whatever")
    return a.value


@decorators.nivs_rt_sequence
def stop_task_in_try():
    try:
        a = I32Value(1)
        with multitask() as mt:
            @task(mt)
            def f1():
                pass

            @task(mt)
            def f2():
                pass
        stop_task(f1)
    finally:
        a.value = 2
    return a.value


@decorators.nivs_rt_sequence
def stop_task_complex():
    a = I32Value(1)
    with multitask() as mt:
        @task(mt)
        def f1():
            nivs_yield()
            a.value = 10

        @task(mt)
        def f2():
            a.value = 2
            stop_task(f1)
    return a.value


@decorators.nivs_rt_sequence
def stop_task_call_subroutine():
    a = DoubleValue(0)
    with multitask() as mt:
        @task(mt)
        def f1():
            nivs_yield()
            a.value = 10

        @task(mt)
        def f2():
            a.value = return_param_plus_1(a)
            stop_task(f1)
    return a.value


@decorators.nivs_rt_sequence
def stop_task_call_subroutine1():
    a = DoubleValue(0)
    with multitask() as mt:
        @task(mt)
        def f1():
            nivs_yield()
            a.value = return_param_plus_1(a)

        @task(mt)
        def f2():
            stop_task(f1)
    return a.value


@decorators.nivs_rt_sequence
def stop_task_call_subroutine2():
    a = DoubleValue(0)
    with multitask() as mt:
        @task(mt)
        def f1():
            a.value = return_param_plus_1(a)
            nivs_yield()
            a.value = return_param_plus_1(a)

        @task(mt)
        def f2():
            stop_task(f1)
    return a.value


run_tests = [
    (stop_task_simple, (), 1),
    (stop_task_in_try, (), 2),
    (stop_task_complex, (), 2),
    (stop_task_call_subroutine, (), 1),
    (stop_task_call_subroutine1, (), 0),
    (stop_task_call_subroutine2, (), 1),
]

skip_tests = [
    (return_param_plus_1, (), "Needs an actual caller."),
]

fail_transform_tests = [
    (stop_task_invalid_task_name, (), VeristandError),
    (stop_task_invalid_task_name1, (), TranslateError),
]


def idfunc(val):
    return val.__name__


@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_transform(func_name, params, expected_result):
    RealTimeSequence(func_name)


@pytest.mark.skip
@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_runpy(func_name, params, expected_result):
    actual = func_name(*params)
    assert actual == expected_result


@pytest.mark.parametrize("func_name, params, expected_result", run_tests, ids=idfunc)
def test_run_in_VM(func_name, params, expected_result):
    actual = rtseqrunner.run_rtseq_in_VM(func_name)
    assert actual == expected_result


@pytest.mark.parametrize("func_name, params, expected_result", fail_transform_tests, ids=idfunc)
def test_failures(func_name, params, expected_result):
    try:
        RealTimeSequence(func_name)
    except expected_result:
        pass
    except VeristandError as e:
        pytest.fail('Unexpected exception raised:' +
                    str(e.__class__) + ' while expected was: ' + expected_result.__name__)
    except Exception as exception:
        pytest.fail('ExpectedException not raised: ' + exception)


@pytest.mark.parametrize("func_name, params, reason", skip_tests, ids=idfunc)
def test_skipped(func_name, params, reason):
    pytest.skip(func_name.__name__ + ": " + reason)


def test_check_all_tested():
    validation.test_validate(sys.modules[__name__])